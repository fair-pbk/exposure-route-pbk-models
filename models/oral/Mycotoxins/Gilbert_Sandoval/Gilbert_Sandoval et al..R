# Human AFB1 PBK with 10-day dosing schedule (deSolve + ggplot)
# Sources for structure/parameters: Gilbert-Sandoval et al. (human model) :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}

library(deSolve)
library(dplyr)
library(tidyr)
library(ggplot2)
library(stringr)

make_params_human <- function() {
  BW <- 70  # kg
  
  # Volumes (fractions from human code)
  VLc <- 0.026 # Liver
  VSc <- 0.627 # Stomach
  VBc <- 0.079 # Blood
  
  Vdd  <- 1.29 # intestinal lumen in L
  VS <- VSc * BW                    # L
  VL <- VLc * BW                    # L
  VB <- VBc * BW                    # L
  Vrest     <<- max(1e-6, 0.84 * BW - VL - Vdd*7 - VB) # L (lumped rest)
  
  # Partitions
  PL <- 1.07
  Prest <- 1.0   # effective lumped value
  
  # Flows (L/h)
  QCc <- 15
  QC <- QCc * BW^0.74 #cardiac output
  QLc <- 0.227 # liver flow fraction
  QL <- QLc * QC
  Qrest <- (1-QLc) * QC
  
  # GI kinetics (human) in 1/h
  ksto <- 2.8   # Stomach emptying rate
  kin  <- 2.19  # Transfer rate between small intestine compartments
  ka   <- 5.05  # absorption rate 
  kfe  <- 0.02  # Transfer rate to feces
  
  Vin <- rep(Vdd, 7) #L
  kabin <- rep(ka * Vdd, 7)   # L/h
  kinv  <- rep(kin, 7)
  
  # Hepatic metabolism (Hill) → AFQ1 & AFBO
  MPL <- 39.46 * 1000                      # mg microsomal/kg liver
  VmaxAFQ1c <- 0.003469                    # umol/(mg microsomal)/min
  VmaxAFBOc <- 0.000542                    # umol/(mg microsomal)/min
  S50AFQ1 <- 427 # umol/h
  nAFQ1 <- 1.2
  S50AFBO <- 197 # umol/h
  nAFBO <- 1.1
  VmaxAFQ1 <- VmaxAFQ1c * 60 * MPL * VL    # umol/h
  VmaxAFBO <- VmaxAFBOc * 60 * MPL * VL    # umol/h
  
  # Molecular weight (for convenience conversions)
  MW <- 312.27
  
  list(
    BW=BW, VL=VL, VB=VB, Vrest=Vrest, PL=PL, Prest=Prest,
    QC=QC, QL=QL, Qrest=Qrest,
    ksto=ksto, Vin=Vin, kabin=kabin, kin=kinv, kfe=kfe,
    VmaxAFQ1=VmaxAFQ1, S50AFQ1=S50AFQ1, nAFQ1=nAFQ1,
    VmaxAFBO=VmaxAFBO, S50AFBO=S50AFBO, nAFBO=nAFBO,
    MW=MW
  )
}

pbk_human <- function(t, A, p) {
  with(as.list(c(A,p)), {
    # Amount states (umol)
    Ast <- A[1]
    Ain <- A[2:8]      # Ain1..Ain7
    Aco <- A[9]
    AFe <- A[10]
    AL  <- A[11]
    AB  <- A[12]
    Arest <- A[13]
    AMAFQ1 <- A[14]
    AMAFBO <- A[15]
    
    # Intestinal concentrations (umol/L)
    Cin <- Ain / Vin
    
    # Stomach
    dAst <- -ksto * Ast
    
    # Intestine chain
    dAin <- numeric(7)
    dAin[1] <- ksto*Ast - kin[1]*Ain[1] - kabin[1]*Cin[1]
    for (i in 2:7) {
      dAin[i] <- kin[i-1]*Ain[i-1] - kin[i]*Ain[i] - kabin[i]*Cin[i]
    }
    
    # Colon and feces
    dAco <- kin[7]*Ain[7] - kfe*Aco
    dAFe <- kfe*Aco
    
    # Blood & tissues (perf.-limited)
    CB <- AB / VB                       # umol/L
    CL <- AL / VL                       # umol/L
    CVL <- CL / PL                      # umol/L
    Crest <- Arest / Vrest              # umol/L
    CVrest <- Crest / Prest             # umol/L
    
    Abs_to_liver <- sum(kabin * Cin)    # umol/h (portal input)
    
    # Liver metabolism (Hill)
    MetAFQ1 <- (VmaxAFQ1 * CVL^nAFQ1) / (S50AFQ1^nAFQ1 + CVL^nAFQ1)
    MetAFBO <- (VmaxAFBO * CVL^nAFBO) / (S50AFBO^nAFBO + CVL^nAFBO)
    
    # Liver amount ODE
    dAL <- QL*(CB - CVL) + Abs_to_liver - MetAFQ1 - MetAFBO
    dAMAFQ1 <- MetAFQ1
    dAMAFBO <- MetAFBO
    
    # Rest of body exchange
    dArest <- Qrest * (CB - CVrest)
    
    # Blood mass balance
    dAB <- QL*CVL + Qrest*CVrest - QC*CB
    
    list(
      c(dAst, dAin, dAco, dAFe, dAL, dAB, dArest, dAMAFQ1, dAMAFBO),
      c(
        # <<< renamed outputs here >>>
        C_blood = CB,
        C_liver = CL,
        C_liver_ven = CVL,
        C_rest = Crest,
        C_in_1 = Cin[1], C_in_2 = Cin[2], C_in_3 = Cin[3],
        C_in_4 = Cin[4], C_in_5 = Cin[5], C_in_6 = Cin[6], C_in_7 = Cin[7],
        Abs_to_liver = Abs_to_liver
      )
    )
  })
}

# -------------------------
# Dosing schedule (10 days)
# -------------------------
p <- make_params_human()

# Define per-dose amount (umol) and timing (hours)
# Example: daily oral bolus at t = 0, 24, ..., 216 h  (10 doses total)
DOSE_mg_per_kg <- 0.000000374                 # use your value here
DOSE_umol_per_kg <- DOSE_mg_per_kg * 1e-3 / p$MW * 1e6
DOSE_umol <- DOSE_umol_per_kg * p$BW         # umol per bolus for this subject

dose_times <- seq(0, by = 24, length.out = 10)  # once daily x 10 days

dosingSchedule <- data.frame(
  var = rep("Ast", length(dose_times)),   # target: stomach amount state
  time = dose_times,                      # dosing times (h)
  value = rep(DOSE_umol, length(dose_times)),  # bolus amount (umol)
  method = rep("add", length(dose_times))      # add amount at 'time'
)

# Simulation window: 10 days
times <- seq(0, 24*10, by = 0.05)  # 0..240 h

# Initial conditions (no initial bolus; dosing via events)
A0 <- c(
  Ast = 0,
  Ain1 = 0, Ain2 = 0, Ain3 = 0, Ain4 = 0, Ain5 = 0, Ain6 = 0, Ain7 = 0,
  Aco = 0, AFe = 0,
  AL = 0, AB = 0, Arest = 0,
  AMAFQ1 = 0, AMAFBO = 0
)

out <- ode(
  y = A0, times = times, func = pbk_human, parms = p,
  method = "lsodes",
  events = list(data = dosingSchedule)
)
out <- as.data.frame(out)

# Ensure clean column names (strip suffix after ".")
names(out) <- sub("\\..*$", "", names(out))

# -------------------------
# Mass balance & outputs
# -------------------------
amount_cols <- c(
  "Ast","Ain1","Ain2","Ain3","Ain4","Ain5","Ain6","Ain7",
  "Aco","AFe","AL","AB","Arest","AMAFQ1","AMAFBO"
)

conc_cols <- c(
  "C_blood","C_liver","C_liver_ven","C_rest",
  "C_in_1","C_in_2","C_in_3","C_in_4","C_in_5","C_in_6","C_in_7"
)

TotalDose_umol <- sum(dosingSchedule$value)

out <- out %>%
  mutate(
    Total_amt = rowSums(across(all_of(amount_cols))),
    MassBal_error_umol = TotalDose_umol - Total_amt,
    MassBal_error_pct  = 100 * (TotalDose_umol - Total_amt) / TotalDose_umol,
    C_blood_ng_mL = C_blood * p$MW / 1e3
  )

# -------------------------
# Plots (amounts, concentrations, mass balance)
# -------------------------
amount_long <- out %>%
  select(time, all_of(amount_cols)) %>%
  pivot_longer(-time, names_to = "compartment", values_to = "amount_umol") %>%
  mutate(group = case_when(
    compartment %in% c("Ast","Ain1","Ain2","Ain3","Ain4","Ain5","Ain6","Ain7","Aco","AFe") ~ "GI & Feces",
    compartment == "AL" ~ "Liver",
    compartment == "AB" ~ "Blood",
    compartment == "Arest" ~ "Rest of body",
    TRUE ~ "Metabolites"
  ))

conc_long <- out %>%
  select(time, all_of(conc_cols)) %>%
  pivot_longer(-time, names_to = "compartment", values_to = "conc_umol_L") %>%
  mutate(group = case_when(
    str_detect(compartment, "^C_in_") ~ "Intestine (subcompartments)",
    compartment %in% c("C_liver") ~ "Liver",
    compartment == "C_blood" ~ "Blood",
    compartment == "C_rest" ~ "Rest of body",
    TRUE ~ "Other"
  ))


g_amounts <- ggplot(amount_long, aes(x = time, y = amount_umol, color = compartment)) +
  geom_line(linewidth = 0.6, alpha = 0.9) +
  facet_wrap(~ group, scales = "free_y") +
  labs(x = "Time (h)", y = "Amount (µmol)",
       title = "AFB1 amounts in all compartments (human PBK) — 10-day dosing") +
  theme_bw() +
  theme(legend.position = "bottom", legend.key.height = unit(0.35, "cm"))

g_conc <- ggplot(conc_long, aes(x = time, y = conc_umol_L, color = compartment)) +
  geom_line(linewidth = 0.6, alpha = 0.9) +
  facet_wrap(~ group, scales = "free_y") +
  labs(x = "Time (h)", y = "Concentration (µmol/L)",
       title = "AFB1 concentrations (human PBK) — 10-day dosing") +
  theme_bw() +
  theme(legend.position = "bottom", legend.key.height = unit(0.35, "cm"))

g_massbal <- ggplot(out, aes(x = time, y = MassBal_error_umol)) +
  geom_hline(yintercept = 0, linetype = 2) +
  geom_line(linewidth = 0.7) +
  labs(x = "Time (h)", y = "Mass balance error (%)",
       title = "Mass balance check (sum of amounts vs. total administered)") +
  theme_bw()

print(g_amounts)
print(g_conc)
print(g_massbal)

# Quick summary
list(
  Total_doses = nrow(dosingSchedule),
  Dose_umol_each = DOSE_umol,
  TotalDose_umol = TotalDose_umol,
  Peak_CB_ng_mL = max(out$CB_ng_mL, na.rm = TRUE),
  Final_mass_balance_error_pct = tail(out$MassBal_error_pct, 1)
)

# --- Build cumulative administered dose over time ---
dose_df <- dosingSchedule |> dplyr::arrange(time)
# at each output time, sum all event doses with event_time <= t  (inclusive)
out <- out |>
  dplyr::rowwise() |>
  dplyr::mutate(
    Dose_to_t_umol = sum(dose_df$value[dose_df$time <= time], na.rm = TRUE)
  ) |>
  dplyr::ungroup()

# --- Mass balance using Dose_to_t (tracks exactly what's been given so far) ---
out <- out |>
  dplyr::mutate(
    Total_amt = rowSums(across(all_of(amount_cols))),
    MB_error_umol = Dose_to_t_umol - Total_amt,
    MB_error_pct  = dplyr::if_else(Dose_to_t_umol > 0,
                                   100 * MB_error_umol / Dose_to_t_umol,
                                   0)
  )

g_massbal <- ggplot(out, aes(time, MB_error_umol)) +
  geom_hline(yintercept = 0, linetype = 2) +
  geom_line() +
  labs(y = "Mass balance error (µmol)",
       title = "Mass balance: (administered to t) − (in system at t)") +
  theme_bw()

print(g_massbal)

