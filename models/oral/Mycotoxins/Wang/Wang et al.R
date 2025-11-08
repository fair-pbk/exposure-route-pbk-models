# Simplified human DON PBK (Wang et al. 2023/2024)
# GI: Stomach -> Jejunum (kab1) -> Ileum (kab2) -> Large intestine (kab3)
# Body: Liver (met) -> Blood <-> Rest
# Features: 10 daily boluses, amounts + concentrations + mass-balance

library(deSolve)
library(dplyr)
library(tidyr)
library(ggplot2)

make_params_wang_human <- function() {
  BW <- 70  # kg
  
  # --- GI transfer rates (human) ---
  ksto <- 1.99   # 1/h stomach -> jejunum
  kin1 <- 2.17   # 1/h jejunum -> ileum
  kin2 <- 0.25   # 1/h ileum -> large intestine  (Kimura & Higaki)  # Wang
  # --- Papp scaling to segment-specific kab (Wang) ---
  # PappDONc = 1.2883 (10^-4 cm/s) -> convert to dm/h, then kab = Papp * SA / Vin
  PappDONc <- 1.2883
  PappDON  <- PappDONc/10000 * 3600/10   # dm/h
  
  D  <- 0.5   # dm (average intestinal diameter)
  L1 <- 30.0  # dm (jejunum length)
  L2 <- 30.0  # dm (ileum length)
  L3 <- 18.7  # dm (large intestine length)
  
  Vin1 <- pi*(D/2)^2 * L1              # L
  SAin1 <- pi*D*L1                     # dm^2
  kab1 <- PappDON * SAin1 / Vin1       # 1/h (jejunum)
  
  Vin2 <- pi*(D/2)^2 * L2              # L
  SAin2 <- pi*D*L2                     # dm^2
  kab2 <- PappDON * SAin2 / Vin2       # 1/h (ileum)
  
  VLU <- 0.561                         # L (large intestine lumen, Wang supp)
  SAin3 <- pi*D*L3                     # dm^2
  kab3 <- PappDON * SAin3 / VLU        # 1/h (large intestine)
  
  # --- Physiology (human) ---
  VLc <- 0.026
  VBc <- 0.079
  VL <- VLc*BW
  VB <- VBc*BW
  
  Vrest <- max(1e-6, 0.84*BW - VL - VB - Vin1 - Vin2 - VLU)         # simple lumped rest volume
  
  # Flows (human; note liver fraction 0.046 in Wang human model)
  QC <- 15 * BW^0.74
  QLc <- 0.046
  QL <- QLc * QC # arterial exchange
  Qrest <- (1 - QLc) * QC
  
  # Hepatic clearance (Wang): CLintDON scaled from microsomes, uses liver-venous conc
  # CLintDONc = 0.008 mL/min/mg; VLM = 32 mg/g; L (g/kg) = VLc*1000
  VLM <- 32
  CLintDONc <- 0.008      # mL/min/mg
  L_g_per_kg <- VLc*1000
  CLintDON <- CLintDONc * VLM * L_g_per_kg * BW * 60 / 1000  # L/h/liver
  
  # Partition (liver/blood) for venous concentration in metabolism term
  RDON <- 0.6523
  PL <- 0.76 / RDON       # liver/blood partition (Wang Table S1)
  
  list(
    # BW & volumes/flows
    BW=BW, VL=VL, VB=VB, Vrest=Vrest, QC=QC, QL=QL, Qrest=Qrest,
    # GI
    ksto=ksto, kin1=kin1, kin2=kin2, Vin1=Vin1, Vin2=Vin2, VLU=VLU,
    kab1=kab1, kab2=kab2, kab3=kab3,
    # Liver clearance & partition
    CLintDON=CLintDON, PL=PL
  )
}

pbk_wang_simple <- function(t, A, p) {
  with(as.list(c(A,p)), {
    # States (µmol)
    Ast  <- A[1]  # stomach lumen
    Ain1 <- A[2]  # jejunum lumen
    Ain2 <- A[3]  # ileum lumen
    ALI  <- A[4]  # large intestine lumen
    AL   <- A[5]  # liver
    AB   <- A[6]  # blood
    Arest<- A[7]  # rest (lumped)
    AMet <- A[8]  # Metabolite
    
    # Concentrations (µmol/L)
    CB   <- AB / VB
    CL   <- AL / VL
    CVL  <- CL / PL           # liver venous
    Crest<- Arest / Vrest
    
    # GI absorption (segment-specific)
    Abs1 <- kab1 * Ain1
    Abs2 <- kab2 * Ain2
    Abs3 <- kab3 * ALI
    Abs_total <- Abs1 + Abs2 + Abs3     # we send absorbed DON directly to liver (simplification)
    
    # Hepatic metabolism (clearance from liver-venous conc, Wang)
    Met <- CLintDON * CVL
    
    # ODEs
    dAst  <- -ksto * Ast
    dAin1 <-  ksto*Ast - kin1*Ain1 - Abs1
    dAin2 <-  kin1*Ain1 - kin2*Ain2 - Abs2
    dALI  <-  kin2*Ain2 - Abs3
    
    dAL   <-  Abs_total + QL*(CB - CVL) - Met
    dAB   <-  QL*CVL + Qrest*Crest - (QL + Qrest)*CB
    dArest<-  Qrest*(CB - Crest)
    dAMet <- Met
    
    list(
      c(dAst,dAin1,dAin2,dALI,dAL,dAB,dArest,dAMet),
      c(
        CB=CB, CL=CL, CVL=CVL, Crest=Crest,
        Cin1 = Ain1/Vin1, Cin2 = Ain2/Vin2, C_LI = ALI/VLU,
        Abs_total = Abs_total, Met = Met
      )
    )
  })
}

# --------------------------
# 10-day once-daily dosing
# --------------------------
p <- make_params_wang_human()

# Example dose: 0.001 mg/kg bw (Wang); adjust as needed
MW <- 296.3
DOSE_mg_perkg <- 0.001
DOSE_umol <- DOSE_mg_perkg * p$BW * 1e-3 / MW * 1e6

dose_times <- seq(0, by = 24, length.out = 10)
dosingSchedule <- data.frame(
  var   = rep("Ast", length(dose_times)),
  time  = dose_times,
  value = rep(DOSE_umol, length(dose_times)),
  method= rep("add", length(dose_times))
)

# Initial conditions
A0 <- c(Ast=0, Ain1=0, Ain2=0, ALI=0, AL=0, AB=0, Arest=0, AMet = 0)

# Simulate 10 days
times <- seq(0, 240, by = 0.1)
out <- ode(y=A0, times=times, func=pbk_wang_simple, parms=p,
           method="lsodes", events=list(data=dosingSchedule)) |>
  as.data.frame()
names(out) <- sub("\\..*$", "", names(out))
# --------------------------
# Mass balance & outputs
# --------------------------
TotalDose_umol <- sum(dosingSchedule$value)

out <- out |>
  mutate(
    Total_amt = Ast + Ain1 + Ain2 + ALI + AL + AB + Arest + AMet,
    MassBal_error_umol = TotalDose_umol - Total_amt,
    MassBal_error_pct  = 100 * (TotalDose_umol - Total_amt) / TotalDose_umol
  )

# Amounts
amount_long <- out |>
  select(time, Ast, Ain1, Ain2, ALI, AL, AB, Arest, AMet) |>
  pivot_longer(-time, names_to="compartment", values_to="amount_umol")

# Concentrations (blood, liver, rest, plus GI lumen concs)
conc_long <- out |>
  select(time, CB, CL, Crest, Cin1, Cin2, C_LI) |>
  pivot_longer(-time, names_to="compartment", values_to="conc_umol_L")

# Plots
g_amounts <- ggplot(amount_long, aes(time, amount_umol, color=compartment)) +
  geom_line() +
  labs(y="Amount (µmol)", title="DON PBK (Wang, simplified): Amounts") +
  theme_bw()

g_conc <- ggplot(conc_long, aes(time, conc_umol_L, color=compartment)) +
  geom_line() +
  labs(y="Concentration (µmol/L)", title="DON PBK (Wang, simplified): Concentrations") +
  theme_bw()

g_massbal <- ggplot(out, aes(time, MassBal_error_umol)) +
  geom_hline(yintercept=0, linetype=2) +
  geom_line() +
  labs(y="Mass balance error (%)", title="Mass balance check") +
  theme_bw()

print(g_amounts)
print(g_conc)
print(g_massbal)


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
    Total_amt = Ast + Ain1 + Ain2 + ALI + AL + AB + Arest + AMet,
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
