# Ou2018_Hg_Human

## Overview

| key                          | value                                         |
|:-----------------------------|:----------------------------------------------|
| Modelled species/orgamism(s) | http://purl.obolibrary.org/obo/NCBITaxon_9606 |
| Model chemical(s)            | http://purl.obolibrary.org/obo/CHEBI_25322    |
| Input route(s)               | 1 (oral)                                      |
| Time resolution              | h                                             |
| Amounts unit                 | ug                                            |
| Volume unit                  | L                                             |
| Number of compartments       | 7                                             |
| Number of species            | 9                                             |
| Number of parameters         | 42 (35 external / 7 internal)                 |

## Diagram

![Diagram](summary.svg)

## Compartments

| id             | name             | unit   | model qualifier                            |
|:---------------|:-----------------|:-------|:-------------------------------------------|
| Gut_lumen      | Gut lumen        | L      | http://purl.obolibrary.org/obo/PBPKO_00478 |
| Gut            | Gut              | L      | http://purl.obolibrary.org/obo/PBPKO_00477 |
| Liver          | Liver            | L      | http://purl.obolibrary.org/obo/PBPKO_00558 |
| Red_Blood_Cell | Red blood cell   | L      | http://purl.obolibrary.org/obo/PBPKO_00634 |
| Plasma         | Plasma           | L      | http://purl.obolibrary.org/obo/PBPKO_00488 |
| Rest           | Rest of the body | L      | http://purl.obolibrary.org/obo/PBPKO_00450 |
| Feces          | Feces            | L      | http://purl.obolibrary.org/obo/PBPKO_00555 |

## Species

| id            | name                                   | unit   | model qualifier                            |
|:--------------|:---------------------------------------|:-------|:-------------------------------------------|
| AGut_lumen    | Amount of chemical in gut lumen        | ug     | *not specified*                            |
| AGut          | Amount of chemical in gut              | ug     | http://purl.obolibrary.org/obo/PBPKO_00496 |
| ALiver        | Amount of chemical in liver            | ug     | http://purl.obolibrary.org/obo/PBPKO_00497 |
| ARBC          | Amount of chemical in red blood cells  | ug     | *not specified*                            |
| APlasma       | Amount of chemical in plasma           | ug     | http://purl.obolibrary.org/obo/PBPKO_00502 |
| ARest         | Amount of chemical in the rest of body | ug     | http://purl.obolibrary.org/obo/PBPKO_00501 |
| ALiver_Met    | Metabolite in liver                    | ug     | http://purl.obolibrary.org/obo/PBPKO_00058 |
| AGutlumen_Met | Metabolite in gut lumen                | ug     | http://purl.obolibrary.org/obo/PBPKO_00058 |
| AFeces        | Cumulative amount of chemical in feces | ug     | http://purl.obolibrary.org/obo/PBPKO_00275 |

## Transfer equations

| id   | from       | to            | equation                                                              |
|:-----|:-----------|:--------------|:----------------------------------------------------------------------|
| _J0  | AGut_lumen | AGut          | $ \mathit{kabs}\cdot \mathit{CGut_{lumen}}\cdot \mathit{Frac}$        |
| _J1  | AGut       | ALiver        | $ \frac{\mathit{QG}\cdot \mathit{CGut}}{\mathit{PGI}}$                |
| _J2  | APlasma    | AGut          | $ \mathit{QG}\cdot \mathit{CPlasma}$                                  |
| _J3  | APlasma    | ALiver        | $ \mathit{QL}\cdot \mathit{CPlasma}$                                  |
| _J4  | ALiver     | APlasma       | $ \frac{(\mathit{QL}+\mathit{QG})\cdot \mathit{CLiver}}{\mathit{PL}}$ |
| _J5  | APlasma    | ARest         | $ \mathit{QRest}\cdot \mathit{CPlasma}$                               |
| _J6  | ARest      | APlasma       | $ \frac{\mathit{QRest}\cdot \mathit{CRest}}{\mathit{PRest}}$          |
| _J7  | APlasma    | ARBC          | $ \mathit{CPlasma}\cdot \mathit{Qrbc}$                                |
| _J8  | ARBC       | APlasma       | $ \frac{\mathit{Qrbc}\cdot \mathit{CRBC}}{\mathit{PRBC}}$             |
| _J9  | ALiver     | AGut_lumen    | $ \mathit{kbiliary}\cdot \mathit{CLiver}$                             |
| _J10 | ALiver     | ALiver_Met    | $ \mathit{kmet_{liver}}\cdot \mathit{CLiver}$                         |
| _J11 | AGut_lumen | AGutlumen_Met | $ \mathit{kmet_{gutlumen}}\cdot \mathit{CGut_{lumen}}$                |
| _J12 | AGut_lumen | AFeces        | $ \mathit{kfe}\cdot \mathit{CGut_{lumen}}$                            |

## ODEs

$\frac{d[\mathtt{AGut-lumen}]}{dt} = -  \mathit{kabs}\cdot \mathit{CGut_{lumen}}\cdot \mathit{Frac}
                   +  \mathit{kbiliary}\cdot \mathit{CLiver}
                   -  \mathit{kmet_{gutlumen}}\cdot \mathit{CGut_{lumen}}
                   -  \mathit{kfe}\cdot \mathit{CGut_{lumen}}$

$\frac{d[\mathtt{AGut}]}{dt} =  \mathit{kabs}\cdot \mathit{CGut_{lumen}}\cdot \mathit{Frac}
             -  \frac{\mathit{QG}\cdot \mathit{CGut}}{\mathit{PGI}}
             +  \mathit{QG}\cdot \mathit{CPlasma}$

$\frac{d[\mathtt{ALiver}]}{dt} =  \frac{\mathit{QG}\cdot \mathit{CGut}}{\mathit{PGI}}
               +  \mathit{QL}\cdot \mathit{CPlasma}
               -  \frac{(\mathit{QL}+\mathit{QG})\cdot \mathit{CLiver}}{\mathit{PL}}
               -  \mathit{kbiliary}\cdot \mathit{CLiver}
               -  \mathit{kmet_{liver}}\cdot \mathit{CLiver}$

$\frac{d[\mathtt{ARBC}]}{dt} =  \mathit{CPlasma}\cdot \mathit{Qrbc}
             -  \frac{\mathit{Qrbc}\cdot \mathit{CRBC}}{\mathit{PRBC}}$

$\frac{d[\mathtt{APlasma}]}{dt} = -  \mathit{QG}\cdot \mathit{CPlasma}
                -  \mathit{QL}\cdot \mathit{CPlasma}
                +  \frac{(\mathit{QL}+\mathit{QG})\cdot \mathit{CLiver}}{\mathit{PL}}
                -  \mathit{QRest}\cdot \mathit{CPlasma}
                +  \frac{\mathit{QRest}\cdot \mathit{CRest}}{\mathit{PRest}}
                -  \mathit{CPlasma}\cdot \mathit{Qrbc}
                +  \frac{\mathit{Qrbc}\cdot \mathit{CRBC}}{\mathit{PRBC}}$

$\frac{d[\mathtt{ARest}]}{dt} =  \mathit{QRest}\cdot \mathit{CPlasma}
              -  \frac{\mathit{QRest}\cdot \mathit{CRest}}{\mathit{PRest}}$

$\frac{d[\mathtt{ALiver-Met}]}{dt} =  \mathit{kmet_{liver}}\cdot \mathit{CLiver}$

$\frac{d[\mathtt{AGutlumen-Met}]}{dt} =  \mathit{kmet_{gutlumen}}\cdot \mathit{CGut_{lumen}}$

$\frac{d[\mathtt{AFeces}]}{dt} =  \mathit{kfe}\cdot \mathit{CGut_{lumen}}$

## Assignment rules

$VRest =  (1-0.122)\cdot \mathit{BW}-\mathit{VGut_{lumen}}-\mathit{VG}-\mathit{VL}-\mathit{VRBC}-\mathit{VPlasma}$

$CGut_lumen =  \frac{\mathit{AGut_{lumen}}}{\mathit{Gut_{lumen}}}$

$CGut =  \frac{\mathit{AGut}}{\mathit{Gut}}$

$CLiver =  \frac{\mathit{ALiver}}{\mathit{Liver}}$

$CRBC =  \frac{\mathit{ARBC}}{\mathit{Red\_Blood\_Cell}}$

$CPlasma =  \frac{\mathit{APlasma}}{\mathit{Plasma}}$

$CRest =  \frac{\mathit{ARest}}{\mathit{Rest}}$

## Initial assignments

$Gut_lumen =  \mathit{VGut_{lumen}}$

$Gut =  \mathit{VG}$

$Liver =  \mathit{VL}$

$Red_Blood_Cell =  \mathit{VRBC}$

$Plasma =  \mathit{VPlasma}$

$Rest =  \mathit{VRest}$

$VGut_lumen =  \mathit{VGut_{lumenc}}\cdot \mathit{BW}$

$VG =  \mathit{VGc}\cdot \mathit{BW}$

$VL =  \mathit{VLc}\cdot \mathit{BW}$

$VRBC =  \mathit{VRBCc}\cdot \mathit{BW}$

$VPlasma =  \mathit{VPlasmac}\cdot \mathit{BW}$

$kabs =  \mathit{kabsc}\cdot {\mathit{BW}}^{0.75}$

$QG =  \mathit{QGc}\cdot \mathit{BW}$

$QL =  \mathit{QLc}\cdot \mathit{QC}$

$QRest =  \mathit{QC}-\mathit{QL}-\mathit{QG}$

$Qrbc =  \mathit{Qrbcc}\cdot {\mathit{BW}}^{0.75}$

$kbiliary =  \mathit{kbiliaryc}\cdot {\mathit{BW}}^{0.75}$

$kmet_liver =  \mathit{kmet_{liverc}}\cdot {\mathit{BW}}^{0.75}$

$kmet_gutlumen =  \mathit{kmet_{gutlumenc}}\cdot {\mathit{BW}}^{0.75}$

$kfe =  \mathit{kfec}\cdot {\mathit{BW}}^{0.75}$

$QC =  20\cdot {\mathit{BW}}^{0.75}$

## Parameters

| id             | name                                            | unit          | model qualifier                            |
|:---------------|:------------------------------------------------|:--------------|:-------------------------------------------|
| VRest          | Volume of rest of the body                      | L             | http://purl.obolibrary.org/obo/PBPKO_00105 |
| BW             | Bodyweight                                      | kg            | http://purl.obolibrary.org/obo/PBPKO_00008 |
| VGut_lumen     | Volume of gut lumen                             | L             | *not specified*                            |
| VG             | Volume of gut                                   | L             | http://purl.obolibrary.org/obo/PBPKO_00524 |
| VL             | Volume of liver                                 | L             | http://purl.obolibrary.org/obo/PBPKO_00077 |
| VRBC           | Volume of red blood cells                       | L             | *not specified*                            |
| VPlasma        | Volume of plasma                                | L             | http://purl.obolibrary.org/obo/PBPKO_00103 |
| CGut_lumen     | Concentration of chemical in gut lumen          | ug/L          | *not specified*                            |
| CGut           | Concentration of chemical in gut                | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00538 |
| CLiver         | Concentration of chemical in liver              | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00539 |
| CRBC           | Concentration of chemical in red blood cells    | ug/L          | *not specified*                            |
| CPlasma        | Concentration of chemical in plasma             | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00549 |
| CRest          | Concentration of chemical in rest of the body   | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00548 |
| kabs           | Absorption rate                                 | L/h           | *not specified*                            |
| Frac           | Coefficient of absorption                       | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00263 |
| QG             | Blood flow to gut                               | L/h           | http://purl.obolibrary.org/obo/PBPKO_00531 |
| PGI            | Partition coefficient Plasma / Gut              | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00166 |
| QL             | Blood flow to liver                             | L/h           | http://purl.obolibrary.org/obo/PBPKO_00024 |
| PL             | Partition coefficient Plasma / Liver            | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00170 |
| QRest          | Blood flow to rest of the body                  | L/h           | http://purl.obolibrary.org/obo/PBPKO_00050 |
| PRest          | Partition coefficient Plasma / Rest of the body | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00518 |
| Qrbc           | Red blood cell / Plasma diffusion               | L/h           | *not specified*                            |
| PRBC           | Plasma / Red blood cell partition coefficient   | dimensionless | *not specified*                            |
| kbiliary       | Biliary rate                                    | L/h           | http://purl.obolibrary.org/obo/PBPKO_00233 |
| kmet_liver     | Hepatic metabolism rate                         | L/h           | http://purl.obolibrary.org/obo/PBPKO_00234 |
| kmet_gutlumen  | Gut lumen metabolism rate                       | L/h           | *not specified*                            |
| kfe            | Fecal excretion rate                            | L/h           | http://purl.obolibrary.org/obo/PBPKO_00230 |
| VGut_lumenc    | Volume fraction of gut lumen                    | dimensionless | *not specified*                            |
| VGc            | Volume fraction of gut lumen                    | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00509 |
| VLc            | Volume fraction of liver                        | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00078 |
| VRBCc          | Volume fraction of red blood cells              | dimensionless | *not specified*                            |
| VPlasmac       | Volume fraction of plasma                       | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00104 |
| kabsc          | Absorption rate constant                        | L/h.kg^-0     | http://purl.obolibrary.org/obo/PBPKO_00141 |
| QGc            | Fraction blood flow to gut                      | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00513 |
| QLc            | Fraction blood flow to liver                    | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00025 |
| QC             | Cardiac output                                  | L/h           | http://purl.obolibrary.org/obo/PBPKO_00013 |
| Qrbcc          | Red blood cell / Plasma diffusion rate          | L/h.kg^-0     | *not specified*                            |
| kbiliaryc      | Biliary rate constant                           | L/h.kg^-0     | *not specified*                            |
| kmet_liverc    | Hepatic metabolism rate constant                | L/h.kg^-0     | *not specified*                            |
| kmet_gutlumenc | Gut lumen metabolism rate constant              | L/h.kg^-0     | *not specified*                            |
| kfec           | Fecal excretion rate constant                   | L/h.kg^-0     | http://purl.obolibrary.org/obo/PBPKO_00236 |
| Age            | Age                                             | y             | http://purl.obolibrary.org/obo/PBPKO_00521 |

## Creators

*not specified*

