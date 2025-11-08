# Human ZEN PBK (Mendez-Catalá et al.) with one "Rest of body" compartment
# Keeps original GI chain (stomach → 7 SI lumen boxes → LI lumen),
# SI tissue (with glucuronidation), liver metabolism (α-ZEL, β-ZEL, ZEN-GLU),
# and adds a single perfusion-limited Rest-of-body that replaces fat/rapid/slow tissues.
# 10 once-daily oral boluses over 10 days; amounts, concentrations, mass balance plots.

library(deSolve)
library(dplyr)
library(tidyr)
library(ggplot2)

make_params_human_ZEN <- function() {
  BW <- 70
  
  # --- Physiological volumes (fractions; human) ---
  VSIc <- 0.009 
  VLc <- 0.026 
  VBc <- 0.074
  VSI <- VSIc*BW
  VL <- VLc*BW
  VB <- VBc*BW 
 
  VMB <- 0.0018  # feces fraction of BW (human),  LI lumen "volume" used for CLIZEN is feces fraction * BW (VMB*BW) in original
  
  VR <- max(1e-6, BW*0.84 - VL - VB - VSI)
  
  # --- Cardiac output and flows (human) ---
  QC  <- 15 * BW^0.74                          # L/h
  QSIc <- 0.181; QLc <- 0.046; QRc <- 0.473; QSc <- 0.248; QFc <- 0.052
  QSI <- QSIc * QC
  QL  <- QLc  * QC
  Qrest <- (1 - QLc - QSIc) * QC
  
  # --- Partition coefficients (ZEN; human) ---
  PIZEN <- 6.56; PLZEN <- 6.56
  PRZEN <- 6.56; PSZEN <- 4.25; PFZEN <- 134.86
  
  # Effective Rest-of-body partition: flow-weighted mix of (rapid, slow, fat)
  Prest_eff <- 1
  
  # --- GI transfer and absorption (human, from original) ---
  ksto <- 2.8
  kin  <- 2.19
  Vin  <- 1.29
  SAin <- 10.3
  PappCaco2ZEN_log <- -4.9829
  PappZEN_dm_per_h <- 10^(0.6836*PappCaco2ZEN_log - 0.5579) * 3600/10  # dm/h
  kabin <- rep(PappZEN_dm_per_h * SAin, 7)  # L/h for each SI segment
  Vin_vec <- rep(Vin, 7)
  kin_vec <- rep(kin, 7)
  kin7_to_LI <- 0.464
  SAinb <- 47.12
  Kb <- PappZEN_dm_per_h * SAinb            # L/h (LI → liver)
  

  
  # --- SI & Liver glucuronidation (Michaelis–Menten, human) ---
  VmaxSIZENGLU <- 0.491/1000 * 60 * 35.2 * (VSIc*1000) * BW  # µmol/h
  KmSIZENGLU   <- 1.174
  VmaxLZENGLU  <- 2.97/1000  * 60 * 120.7 * (VLc*1000) * BW  # µmol/h
  KmLZENGLU    <- 2.043
  
  # --- Liver α-ZEL / β-ZEL formation (MM; human) ---
  VmaxLaZEL <- 358.7/1e6 * 60 * 120.7 * (VLc*1000) * BW   # µmol/h
  KmLaZEL   <- 9
  VmaxLbZEL <- 209.3/1e6 * 60 * 120.7 * (VLc*1000) * BW   # µmol/h
  KmLbZEL   <- 23
  
  # --- Excretion (keep pools so mass balance closes) ---
  KurZ <- 0.096   # h^-1 (urinary from blood)
  KfeZ <- 0.024   # h^-1 (fecal from LI ZEN)
  
  list(
    # Body & flows
    BW=BW, VSI=VSI, VL=VL, VB=VB,VR=VR, QC=QC, QSI=QSI, QL=QL, Qrest=Qrest,
    # Partitions
    PIZEN=PIZEN, PLZEN=PLZEN, Prest=Prest_eff,
    # GI chain
    ksto=ksto, Vin=Vin_vec, SAin=SAin, kin=kin_vec, kabin=kabin,
    kin7_to_LI=kin7_to_LI, Kb=Kb,
    # Microbial scaling
    VMB=VMB,
    # SI & Liver kinetics
    VmaxSIZENGLU=VmaxSIZENGLU, KmSIZENGLU=KmSIZENGLU,
    VmaxLZENGLU=VmaxLZENGLU,   KmLZENGLU=KmLZENGLU,
    VmaxLaZEL=VmaxLaZEL, KmLaZEL=KmLaZEL,
    VmaxLbZEL=VmaxLbZEL, KmLbZEL=KmLbZEL,
    # Excretion
    KurZ=KurZ, KfeZ=KfeZ
  )
}

pbk_human_ZEN_rest <- function(t, A, p) {
  with(as.list(c(A,p)), {
    # States (µmol)
    Ast <- A["Ast"]
    Ain <- A[paste0("Ain", 1:7)]
    ASI <- A["ASIZEN"]
    ASI_GLU <- A["ASIZENGLU"]
    ALI <- A["ALIZEN"]
    AL  <- A["ALZEN"]
    AB  <- A["AB"]
    Arest <- A["Arest"]
    ALa <- A["ALaZEL"]
    ALb <- A["ALbZEL"]
    AL_GLU <- A["ALZENGLU"]
    AZur <- A["AZur"]
    AZfe <- A["AZfe"]
    
    # Concentrations (µmol/L)
    CB <- AB/VB
    CSI <- ASI / VSI
    CVSIZEN <- CSI / PIZEN
    
    CL <- AL / VL
    CVLZEN <- CL / PLZEN
    
    Crest <- Arest / ( Vrest)  # use total rest volume (fractions * BW)
    CVrest <- Crest / Prest
    
    Cin <- Ain / Vin
    CLIZEN <- ALI / (VMB * BW)               # original human code
    
    # Stomach
    dAst <- -ksto*Ast
    
    # SI lumen chain
    dAin <- numeric(7)
    dAin[1] <- ksto*Ast - kin[1]*Ain[1] - kabin[1]*Cin[1]
    for(i in 2:7){
      dAin[i] <- kin[i-1]*Ain[i-1] - kin[i]*Ain[i] - kabin[i]*Cin[i]
    }
    
    # SI tissue uptake and glucuronidation
    Abs_SI <- sum(kabin * Cin)                      # L/h * µmol/L = µmol/h
    v_SI_GLU <- VmaxSIZENGLU * CVSIZEN / (KmSIZENGLU + CVSIZEN)
    
    dASI     <- Abs_SI + QSI*(CB - CVSIZEN) - v_SI_GLU
    dASI_GLU <- v_SI_GLU
    
    # LI lumen (microbiota term kept in structure; α/β-ZEL amounts are tracked as formed)
    # Here we only need parent ZEN mass paths; keep microbial conversions symbolic if desired
    # For strict parent mass balance, count LI loss to feces and to liver via Kb*CLIZEN:
    dALI <- kin7_to_LI*Ain[7] - Kb*CLIZEN - KfeZ*ALI
    
    # Liver metabolism (MM) from liver-venous (CVLZEN)
    v_L_aZEL   <- VmaxLaZEL  * CVLZEN / (KmLaZEL  + CVLZEN)
    v_L_bZEL   <- VmaxLbZEL  * CVLZEN / (KmLbZEL  + CVLZEN)
    v_L_ZENGLU <- VmaxLZENGLU* CVLZEN / (KmLZENGLU+ CVLZEN)
    
    # Liver amount balance (portal: QSI*CVSIZEN, LI to liver: Kb*CLIZEN)
    dAL <- QL*CB + QSI*CVSIZEN - (QL+QSI)*CVLZEN - v_L_aZEL - v_L_bZEL - v_L_ZENGLU + Kb*CLIZEN
    dALa <- v_L_aZEL
    dALb <- v_L_bZEL
    dAL_GLU <- v_L_ZENGLU
    
    # Rest-of-body (perfusion-limited single lump)
    dArest <- Qrest*(CB - CVrest)
    
    # Blood (include return from liver venous and rest venous; urinary excretion from blood)
    dAB <- (QL+QSI)*CVLZEN + Qrest*CVrest - (QL+QSI+Qrest)*CB - KurZ*AB
    
    # Excretion pools
    dAZur <- KurZ*AB
    dAZfe <- KfeZ*ALI
    
    list(
      c(
        dAst,
        setNames(dAin, paste0("Ain",1:7)),
        dASI, dASI_GLU,
        dALI,
        dAL, dAB, dArest,
        dALa, dALb, dAL_GLU,
        dAZur, dAZfe
      ),
      c(
        # convenient outputs
        CB=CB, CL=CL, CVSIZEN=CVSIZEN, CVLZEN=CVLZEN, Crest=Crest,
        Cin1=Cin[1], Cin2=Cin[2], Cin3=Cin[3], Cin4=Cin[4], Cin5=Cin[5], Cin6=Cin[6], Cin7=Cin[7],
        CLIZEN=CLIZEN,
        Abs_SI=Abs_SI, L_met_a=v_L_aZEL, L_met_b=v_L_bZEL, L_GLU=v_L_ZENGLU
      )
    )
  })
}

# ----------------------
# Dosing: 10 daily bolus
# ----------------------
p <- make_params_human_ZEN()
MW_ZEN <- 318.37
DOSE_mg_perkg <- 0.008   # example; adjust as needed
DOSE_umol <- DOSE_mg_perkg * p$BW * 1e3 / MW_ZEN  # mg→µmol

dose_times <- seq(0, by=24, length.out=10)
events <- data.frame(
  var   = "Ast",
  time  = dose_times,
  value = rep(DOSE_umol, length(dose_times)),
  method= "add"
)

# Initial conditions
A0 <- c(
  Ast=0,
  setNames(rep(0,7), paste0("Ain",1:7)),
  ASIZEN=0, ASIZENGLU=0,
  ALIZEN=0,
  ALZEN=0, AB=0, Arest=0,
  ALaZEL=0, ALbZEL=0, ALZENGLU=0,
  AZur=0, AZfe=0
)

times <- seq(0, 24*10, by=0.05)

out <- ode(y=A0, times=times, func=pbk_human_ZEN_rest, parms=p,
           method="lsodes", events=list(data=events)) |>
  as.data.frame()
names(out) <- sub("\\..*$", "", names(out))

# ----------------------
# Mass balance (parent + tracked products/excreta)
# ----------------------
TotalDose_umol <- sum(events$value)

amount_cols <- c(
  "Ast", paste0("Ain",1:7), "ASIZEN","ASIZENGLU","ALIZEN",
  "ALZEN","AB","Arest","ALaZEL","ALbZEL","ALZENGLU","AZur","AZfe"
)

out <- out |>
  mutate(
    Total_amt = rowSums(across(all_of(amount_cols))),
    MB_err_umol = TotalDose_umol - Total_amt,
    MB_err_pct  = 100 * MB_err_umol / TotalDose_umol
  )

# ----------------------
# Long data & plots
# ----------------------
amt_long <- out |>
  select(time, all_of(amount_cols)) |>
  pivot_longer(-time, names_to="compartment", values_to="amount_umol") |>
  mutate(group = case_when(
    grepl("^Ain|^Ast$|^ALIZEN$|^AZfe$", compartment) ~ "GI & Feces",
    compartment %in% c("ASIZEN","ASIZENGLU") ~ "SI Tissue",
    compartment %in% c("ALZEN","ALaZEL","ALbZEL","ALZENGLU") ~ "Liver (parent & mets)",
    compartment == "AB" ~ "Blood",
    compartment == "Arest" ~ "Rest of body",
    compartment == "AZur" ~ "Urine",
    TRUE ~ "Other"
  ))

conc_long <- out |>
  select(time, CB, CL, CVSIZEN, CVLZEN, Crest, starts_with("Cin")) |>
  pivot_longer(-time, names_to="compartment", values_to="conc_umol_L") |>
  mutate(group = case_when(
    grepl("^Cin", compartment) ~ "SI lumen (segments)",
    compartment == "CVSIZEN" ~ "SI Tissue venous",
    compartment == "CVLZEN" ~ "Liver venous",
    compartment == "CL" ~ "Liver",
    compartment == "CB" ~ "Blood",
    compartment == "Crest" ~ "Rest of body",
    TRUE ~ "Other"
  ))

g_amt <- ggplot(amt_long, aes(time, amount_umol, color=compartment)) +
  geom_line(linewidth=0.6) +
  facet_wrap(~group, scales="free_y") +
  labs(x="Time (h)", y="Amount (µmol)", title="ZEN PBK (human): amounts") +
  theme_bw() + theme(legend.position="bottom")

g_conc <- ggplot(conc_long, aes(time, conc_umol_L, color=compartment)) +
  geom_line(linewidth=0.6) +
  facet_wrap(~group, scales="free_y") +
  labs(x="Time (h)", y="Concentration (µmol/L)", title="ZEN PBK (human): concentrations") +
  theme_bw() + theme(legend.position="bottom")

g_mb <- ggplot(out, aes(time, MB_err_umol)) +
  geom_hline(yintercept=0, linetype=2) +
  geom_line(linewidth=0.7) +
  labs(x="Time (h)", y="Mass-balance error (µmol)", title="Mass balance check") +
  theme_bw()

print(g_amt); print(g_conc); print(g_mb)

list(
  doses = nrow(events),
  dose_umol_each = DOSE_umol,
  total_dose_umol = TotalDose_umol,
  final_mass_balance_error_pct = tail(out$MB_err_pct, 1)
)
