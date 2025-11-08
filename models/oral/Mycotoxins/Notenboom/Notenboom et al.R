# DON PBK model (Notenboom et al. 2023)
# Structure: GI lumen (Lumen) -> Liver -> Blood <-> Rest, with metabolism in Liver
# Multiple daily boluses over 10 days
# Sources: 

library(deSolve)
library(dplyr)
library(tidyr)
library(ggplot2)

make_params_don <- function() {
  BW <- 70  # kg
  
  # GI absorption
  ka <- 22   # 1/h
  
  # Metabolic C_Liver clearance (L/h/kg → scaled to BW)
  C_Liver_met_3G <- 0.07 * BW   # L/h
  C_Liver_met_15G <- 0.32 * BW  # L/h
  
  # Volumes (L)
  VLiverc <- 0.026
  VBloodc <- 0.079 
  
  VLiver <-  VLiverc * BW   # liver
  VBlood <-  VBloodc * BW   # blood
  
  VRest <- 0.84 * BW - VLiver - VBlood   # lumped rest
  VLumen<- 1.29       # lumen
  
  # Flows (L/h):contentReference[oaicite:4]{index=4}
  QC <- 15 * BW^0.74
  
  QLiverc <- 0.227
  QLiver <- QLiverc * QC
  QRest <- (1 - QLiverc) * QC
  
  
  PLiver = 6.56
  PRest = 1
  
  list(
    BW=BW, ka=ka,
    C_Liver_met_3G=C_Liver_met_3G, C_Liver_met_15G=C_Liver_met_15G,
    VLiver=VLiver, VBlood=VBlood, VRest=VRest, VLumen=VLumen,
    QC=QC, QLiver=QLiver, QRest=QRest, PLiver = PLiver, PRest = PRest
  )
}

pbk_don <- function(t, A, p) {
  with(as.list(c(A,p)), {
    # States
    ALumen <- A[1]   # GI lumen
    ALiver <- A[2]    # Liver
    ABlood <- A[3]    # Blood
    ARest <- A[4] # Rest
    AM3G <- A[5]  # DON-3-GlcA formed
    AM15G <- A[6] # DON-15-GlcA formed
    
    # Concentrations
    C_Liver <- ALiver/VLiver
    C_Blood <- ABlood/VBlood
    C_Rest <- ARest/VRest
    
    # Metabolism
    Met3G <- C_Liver_met_3G * C_Liver
    Met15G <- C_Liver_met_15G * C_Liver
    
    # ODEs
    dALumen <- - ka * ALumen
    dALiver <- ka * ALumen + QLiver*(C_Blood - C_Liver/PLiver) - Met3G -Met15G
    dABlood <- QLiver*(C_Liver/PLiver) + QRest*(C_Rest/PRest) - QC*C_Blood
    dARest <- QRest*(C_Blood - C_Rest/PRest)
    
    dAM3G <- Met3G
    dAM15G <- Met15G
    
    list(
      c(dALumen,dALiver,dABlood,dARest,dAM3G,dAM15G),
      c(C_Blood=C_Blood,C_Liver=C_Liver,C_Rest=C_Rest)
    )
  })
}

# --------------------------
# Simulation with daily dosing
# --------------------------
p <- make_params_don()

# 1 mg bolus DON (MW = 296 g/mol ≈ 3.38 µmol)
MW <- 296
DOSE_mg <- 1
DOSE_umol <- DOSE_mg*1e-3/MW*1e6

# 10 daily doses (every 24 h)
dose_times <- seq(0, by = 24, length.out = 10)
dosingSchedule <- data.frame(
  var = rep("ALumen", length(dose_times)),   # target = lumen
  time = dose_times,                      # dosing times
  value = rep(DOSE_mg, length(dose_times)),
  method = rep("add", length(dose_times))
)

# Initial conditions (no baseline dose)
A0 <- c(ALumen=0, ALiver=0, ABlood=0, ARest=0, AM3G=0, AM15G=0)

# Simulate 10 days (240 h)
times <- seq(0, 240, by=0.1)

out <- ode(
  y=A0, times=times, func=pbk_don, parms=p, method="lsodes",
  events=list(data=dosingSchedule)
)
out <- as.data.frame(out)
names(out) <- sub("\\..*$", "", names(out))

# --- Mass balance ---
TotalDose_umol <- sum(dosingSchedule$value)
out <- out %>%
  mutate(
    Total_amt = ALumen + ALiver + ABlood + ARest + AM3G + AM15G,
    MassBal_error_umol = TotalDose_umol - Total_amt,
    MassBal_error_pct  = 100 * (TotalDose_umol - Total_amt) / TotalDose_umol
  )

# --- Plot amounts ---
amount_long <- out %>%
  select(time,ALumen,ALiver,ABlood,ARest,AM3G,AM15G) %>%
  pivot_longer(-time,names_to="compartment",values_to="amount_umol")

g_amounts <- ggplot(amount_long,aes(time,amount_umol,color=compartment))+
  geom_line()+
  labs(y="Amount (µmol)",title="DON PBK: Amounts (10 daily boluses)")+
  theme_bw()

# --- Plot concentrations ---
conc_long <- out %>%
  select(time,C_Blood,C_Liver,C_Rest) %>%
  pivot_longer(-time,names_to="compartment",values_to="conc_umol_L")

g_conc <- ggplot(conc_long,aes(time,conc_umol_L,color=compartment))+
  geom_line()+
  labs(y="Concentration (µmol/L)",title="DON PBK: Concentrations (10 daily boluses)")+
  theme_bw()

# --- Plot mass balance ---
g_massbal <- ggplot(out,aes(time,MassBal_error_pct))+
  geom_hline(yintercept=0,linetype=2)+
  geom_line()+
  labs(y="Mass balance error (%)",title="DON PBK: Mass balance check")+
  theme_bw()

print(g_amounts)
print(g_conc)
print(g_massbal)

# --- Build cumulative administered dose over time ---
dose_df <- dosingSchedule |> dplyr::arrange(time)

out <- out |>
  dplyr::rowwise() |>
  dplyr::mutate(
    Dose_to_t_umol = sum(dose_df$value[dose_df$time <= time], na.rm = TRUE)
  ) |>
  dplyr::ungroup()

# --- Mass balance using Dose_to_t (tracks exactly what's been given so far) ---
out <- out |>
  dplyr::mutate(
    Total_amt = ALumen + ALiver + ABlood + ARest + AM3G + AM15G,
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

