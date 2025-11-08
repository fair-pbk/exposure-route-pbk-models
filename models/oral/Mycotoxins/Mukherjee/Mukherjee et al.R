# Human ZEN (parent-only) PBK per Mukherjee GI (fast/slow lumen) + Rest
# - GI lumen -> fast lumen (KFL) & slow lumen (KSL)
# - Absorption from fast lumen to Gut tissue (Kabs * C_fast * V_fast)
# - Slow lumen -> Colon (Kel * C_slow * V_slow)
# - Perfusion-limited: Gut tissue <-> Blood, Liver <-> Blood, Rest <-> Blood
# - Liver metabolism of parent (first-order by default, MM optional)
# - 10 once-daily oral boluses; amounts + concentrations + mass balance
# Sources for structure/kinetics: Mukherjee et al. human model (Eqs. 2–6, 8–11; Table 1). 

library(deSolve)
library(dplyr)
library(tidyr)
library(ggplot2)

make_params_mukherjee_human <- function() {
  BW <- 70
  
  # --- Cardiac output & flows (human) ---
  QC   <- 15 * BW^0.74        # L/h
  QLc  <- 0.046               # liver fraction
  QGc  <- 0.181               # gut tissue fraction (small intestine)
  QL   <- QLc * QC
  QG   <- QGc * QC
  Qrest <- (1 - QLc - QGc) * QC
  
  # --- Volumes (L) ---
  # Tissue volumes follow Brown (fractions), lumen volumes set explicitly.
  VLc <- 0.026; VBc <- 0.074   # liver, blood (fraction BW)
  VGc <- 0.009                 # small-intestine tissue (fraction BW) per Brown; used as "Gut tissue"
  VL  <- VLc * BW
  VB  <- VBc * BW
  VG  <- VGc * BW
  Vrest <- max(1e-6, 0.84*BW - VL - VB - VG)  # lumped rest-of-body (similar to earlier builds)
  
  # GI lumen volumes (Mukherjee model uses VGL, VFL, VSL, VCo). Set workable defaults.
  VGL <- 1.0    # GI lumen "stomach/upper lumen" (L)
  VFL <- 0.7    # Fast lumen (L)
  VSL <- 0.7    # Slow lumen (L)
  VCo <- 0.56   # Colon lumen (L) ~ large intestine lumen scale
  
  # --- Partition coefficients (ZEN; human) ---
  # Use intestine/liver values consistent with ZEN PBK (intestine & liver ~6.56), rest ~4.25.
  PG <- 6.56   # gut tissue:blood
  PL <- 6.56   # liver:blood
  Prest <- 4.25
  # blood is reference
  
  # --- GI kinetic rate constants (h^-1), Mukherjee (Table 1, human ZEA) ---
  KFL  <- 20.0   # GI lumen -> Fast lumen
  KSL  <- 0.05   # GI lumen -> Slow lumen
  Kel  <- 3.45   # Slow lumen -> Colon
  Kabs <- 15.45  # Fast lumen -> Gut tissue (absorptive flux)
  
  # Optional excretion loops (default 0 to avoid mass leaving system):
  Kex  <- 0.0    # Colon -> feces (set 0.0004 to mimic Table 1 and include AFeces in MB)
  Krel <- 0.0    # Liver -> bile (set >0 to enable, and bile->GI recirculation handled below)
  
  Qbile <- 0.0   # L/h, set >0 with Krel to use bile recirculation
  Vbile <- 0.2   # L, if bile is enabled
  
  # --- Hepatic metabolism of parent (choose either 1st-order or MM). ---
  kmet <- 0.2   # 1/h, first-order metabolic clearance from liver (Parent -> AMet)
  Vm   <- 0.0   # µmol/h/L (set >0 to engage MM below)
  Km   <- 1.0   # µmol/L
  
  list(
    # BW & volumes
    BW=BW, VL=VL, VB=VB, VG=VG, Vrest=Vrest,
    VGL=VGL, VFL=VFL, VSL=VSL, VCo=VCo, Vbile=Vbile,
    # flows
    QC=QC, QL=QL, QG=QG, Qrest=Qrest, Qbile=Qbile,
    # partitions
    PG=PG, PL=PL, Prest=Prest,
    # GI rates
    KFL=KFL, KSL=KSL, Kel=Kel, Kabs=Kabs, Kex=Kex, Krel=Krel,
    # liver metabolism
    kmet=kmet, Vm=Vm, Km=Km
  )
}

pbk_mukherjee <- function(t, A, p) {
  with(as.list(c(A, p)), {
    # --- States (amounts, µmol) ---
    # GI
    AGI    <- A[1]  # GI lumen "stomach/upper lumen"
    Afast  <- A[2]  # Fast lumen
    Aslow  <- A[3]  # Slow lumen
    Acolon <- A[4]  # Colon lumen
    # Tissues
    AGut   <- A[5]  # Gut tissue
    AL     <- A[6]  # Liver
    AB     <- A[7]  # Blood
    Arest  <- A[8]  # Rest of body
    # Optional sinks/recirc
    Abile  <- A[9]  # Bile pool (if enabled)
    AFeces <- A[10] # Feces accumulator
    AMet   <- A[11] # Metabolized parent accumulator
    
    # --- Concentrations (µmol/L) ---
    C_GI    <- AGI   / VGL
    C_fast  <- Afast / VFL
    C_slow  <- Aslow / VSL
    C_colon <- Acolon/ VCo
    
    C_gut   <- AGut  / VG
    C_liv   <- AL    / VL
    C_bld   <- AB    / VB
    C_rest  <- Arest / Vrest
    
    # Tissue venous-side (partition-limited) concentrations for exchange
    Cvgut   <- C_gut / PG
    Cvliv   <- C_liv / PL
    Cvrest  <- C_rest/ Prest
    
    # --- GI fluxes (Mukherjee Eqs. 2–5; Table 1 rates) ---
    # GI lumen splits into fast & slow lumens
    GI_to_fast <- KFL * C_GI * VGL
    GI_to_slow <- KSL * C_GI * VGL
    slow_to_colon <- Kel * C_slow * VSL
    fast_absorb   <- Kabs * C_fast * VFL         # to Gut tissue
    
    # Fecal excretion (optional, tracked to AFeces so mass is closed)
    colon_to_feces <- Kex * C_colon * VCo
    
    # --- Perfusion-limited exchanges (Gut/Liver/Rest with Blood) ---
    # Flux positive into tissue amounts
    Gut_from_blood   <- QG * (C_bld - Cvgut)
    Liv_from_blood   <- QL * (C_bld - Cvliv)
    Rest_from_blood  <- Qrest * (C_bld - Cvrest)
    
    # --- Liver metabolism (parent only) ---
    if (Vm > 0) {
      Met <- Vm * C_liv / (Km + C_liv)   # Michaelis–Menten (µmol/h)
    } else {
      Met <- kmet * AL                    # first-order in amount (µmol/h)
    }
    
    # --- Bile recirculation (optional) ---
    # Liver -> bile (rate ~ Krel * CL * Qbile), bile -> GI lumen (simple flow back)
    Liv_to_bile <- Qbile * (Krel * C_liv - (Abile / Vbile))
    Bile_to_GI  <- Qbile * (Abile / Vbile)   # same Qbile used for return; simple well-mixed bile
    
    # --- ODEs ---
    dAGI    <- -GI_to_fast - GI_to_slow + Bile_to_GI
    dAfast  <-  GI_to_fast - fast_absorb
    dAslow  <-  GI_to_slow - slow_to_colon
    dAcolon <-  slow_to_colon - colon_to_feces
    
    dAGut   <-  fast_absorb + Gut_from_blood
    dAL     <-  Liv_from_blood - Met - Liv_to_bile
    dAB     <-  (QL * Cvliv + QG * Cvgut + Qrest * Cvrest) - (QL + QG + Qrest) * C_bld
    dArest  <-  Rest_from_blood
    
    dAbile  <-  Liv_to_bile - Bile_to_GI
    dAFeces <-  colon_to_feces
    dAMet   <-  Met
    
    list(
      c(dAGI, dAfast, dAslow, dAcolon, dAGut, dAL, dAB, dArest, dAbile, dAFeces, dAMet),
      c(
        CBlood = C_bld, CLiver = C_liv, CGut = C_gut, CRest = C_rest,
        C_GI = C_GI, C_Fast = C_fast, C_Slow = C_slow, C_Colon = C_colon,
        Abs_flux = fast_absorb, Met_flux = Met
      )
    )
  })
}

# -------------------------
# 10-day once-daily dosing
# -------------------------
p <- make_params_mukherjee_human()

# Example oral dose (set yours): mg/kg -> µmol per bolus
MW <- 318.37   # ZEN (swap if needed)
DOSE_mg_perkg <- 0.001
DOSE_umol <- DOSE_mg_perkg * p$BW * 1e-3 / MW * 1e6

dose_times <- seq(0, by = 24, length.out = 10)
dosingSchedule <- data.frame(
  var   = rep("AGI", length(dose_times)),  # to GI lumen (Mukherjee "Intake" into GI)
  time  = dose_times,
  value = rep(DOSE_umol, length(dose_times)),
  method= rep("add", length(dose_times))
)

# Initial amounts
A0 <- c(
  AGI=0, Afast=0, Aslow=0, Acolon=0,
  AGut=0, AL=0, AB=0, Arest=0,
  Abile=0, AFeces=0, AMet=0
)

# Solve
times <- seq(0, 24*10, by = 0.05)
out <- ode(y = A0, times = times, func = pbk_mukherjee, parms = p,
           method = "lsodes", events = list(data = dosingSchedule)) %>% as.data.frame()
names(out) <- sub("\\..*$", "", names(out))

# -------------------------
# Mass balance & outputs
# -------------------------
TotalDose_umol <- sum(dosingSchedule$value)

amount_cols <- c("AGI","Afast","Aslow","Acolon","AGut","AL","AB","Arest","Abile","AFeces","AMet")
conc_cols   <- c("CBlood","CLiver","CGut","CRest","C_GI","C_Fast","C_Slow","C_Colon")

out <- out %>%
  mutate(
    Total_amt = rowSums(across(all_of(amount_cols))),
    MassBal_error_umol = TotalDose_umol - Total_amt,
    MassBal_error_pct  = 100 * (TotalDose_umol - Total_amt) / TotalDose_umol
  )

# Long forms
amount_long <- out %>%
  select(time, all_of(amount_cols)) %>%
  pivot_longer(-time, names_to = "compartment", values_to = "amount_umol") %>%
  mutate(group = case_when(
    compartment %in% c("AGI","Afast","Aslow","Acolon") ~ "GI lumen chain",
    compartment == "AGut" ~ "Gut tissue",
    compartment == "AL" ~ "Liver",
    compartment == "AB" ~ "Blood",
    compartment == "Arest" ~ "Rest of body",
    TRUE ~ "Excretion/Met"
  ))

conc_long <- out %>%
  select(time, all_of(conc_cols)) %>%
  pivot_longer(-time, names_to = "compartment", values_to = "conc_umol_L") %>%
  mutate(group = case_when(
    grepl("^C_", compartment) ~ "GI lumen",
    compartment == "CGut" ~ "Gut tissue",
    compartment == "CLiver" ~ "Liver",
    compartment == "CBlood" ~ "Blood",
    compartment == "CRest" ~ "Rest of body",
    TRUE ~ "Other"
  ))

# Plots
g_amounts <- ggplot(amount_long, aes(time, amount_umol, color = compartment)) +
  geom_line(linewidth = 0.6) +
  facet_wrap(~ group, scales = "free_y") +
  labs(x = "Time (h)", y = "Amount (µmol)",
       title = "ZEN amounts — human PBK (Mukherjee GI, +Rest) — 10 daily boluses") +
  theme_bw() + theme(legend.position = "bottom")

g_conc <- ggplot(conc_long, aes(time, conc_umol_L, color = compartment)) +
  geom_line(linewidth = 0.6) +
  facet_wrap(~ group, scales = "free_y") +
  labs(x = "Time (h)", y = "Concentration (µmol/L)",
       title = "ZEN concentrations — human PBK (Mukherjee GI, +Rest)") +
  theme_bw() + theme(legend.position = "bottom")

g_massbal <- ggplot(out, aes(time, MassBal_error_umol)) +
  geom_hline(yintercept = 0, linetype = 2) +
  geom_line(linewidth = 0.7) +
  labs(x = "Time (h)", y = "Mass balance error (µmol)",
       title = "Mass balance (total dose minus total system amount)") +
  theme_bw()

print(g_amounts)
print(g_conc)
print(g_massbal)

tail(out %>% select(time, Total_amt, MassBal_error_umol, MassBal_error_pct), 3)
