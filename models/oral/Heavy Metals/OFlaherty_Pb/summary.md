# OFlaherty2000_Pb_Human_Male

## Overview

| key                          | value                                         |
|:-----------------------------|:----------------------------------------------|
| Modelled species/orgamism(s) | http://purl.obolibrary.org/obo/NCBITaxon_9606 |
| Model chemical(s)            | *not specified*                               |
| Input route(s)               | *no routes detected*                          |
| Time resolution              | h                                             |
| Amounts unit                 | ug                                            |
| Volume unit                  | L                                             |
| Number of compartments       | 3                                             |
| Number of species            | 3                                             |
| Number of parameters         | 21 (17 external / 4 internal)                 |

## Diagram

![Diagram](summary.svg)

## Compartments

| id    | name             | unit   | model qualifier                            |
|:------|:-----------------|:-------|:-------------------------------------------|
| Liver | Liver            | L      | http://purl.obolibrary.org/obo/PBPKO_00558 |
| Blood | Blood            | L      | http://purl.obolibrary.org/obo/PBPKO_00464 |
| Rest  | Rest of the body | L      | http://purl.obolibrary.org/obo/PBPKO_00450 |

## Species

| id     | name                                   | unit   | model qualifier                            |
|:-------|:---------------------------------------|:-------|:-------------------------------------------|
| ALiver | Amount of chemical in liver            | ug     | http://purl.obolibrary.org/obo/PBPKO_00497 |
| ABlood | Amount of chemical in blood            | ug     | http://purl.obolibrary.org/obo/PBPKO_00623 |
| ARest  | Amount of chemical in the rest of body | ug     | http://purl.obolibrary.org/obo/PBPKO_00501 |

## Transfer equations

| id   | from   | to     | equation                                                                                                                                                                                                                                                                                            |
|:-----|:-------|:-------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _J0  | ALiver | ABlood | $ \mathit{QL}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}+\mathit{Htc}\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}})$                   |
| _J1  | ABlood | ALiver | $ \mathit{QL}\cdot \mathit{CBlood}$                                                                                                                                                                                                                                                                 |
| _J2  | ARest  | ABlood | $ \mathit{QRest}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}+\mathit{Htc}\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}})$ |
| _J3  | ABlood | ARest  | $ \mathit{QRest}\cdot \mathit{CBlood}$                                                                                                                                                                                                                                                              |

## ODEs

$\frac{d[\mathtt{ALiver}]}{dt} = -  \mathit{QL}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}+\mathit{Htc}\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}})
               +  \mathit{QL}\cdot \mathit{CBlood}$

$\frac{d[\mathtt{ABlood}]}{dt} =  \mathit{QL}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}+\mathit{Htc}\cdot \frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ALiver}}{\mathit{VL}\cdot \mathit{PL}}})
               -  \mathit{QL}\cdot \mathit{CBlood}
               +  \mathit{QRest}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}+\mathit{Htc}\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}})
               -  \mathit{QRest}\cdot \mathit{CBlood}$

$\frac{d[\mathtt{ARest}]}{dt} = -  \mathit{QRest}\cdot (1-\mathit{Htc})\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}+\mathit{Htc}\cdot \frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}\cdot (\mathit{G}+\frac{\mathit{BIND}}{\mathit{KBIND}+\frac{\mathit{ARest}}{\mathit{VRest}\cdot \mathit{PRest}}})
              +  \mathit{QRest}\cdot \mathit{CBlood}$

## Assignment rules

$VRest =  \mathit{BW}-\mathit{VL}-\mathit{VB}$

$CLiver =  \frac{\mathit{ALiver}}{\mathit{Liver}}$

$CBlood =  \frac{\mathit{ABlood}}{\mathit{Blood}}$

$CRest =  \frac{\mathit{ARest}}{\mathit{Rest}}$

## Initial assignments

$Liver =  \mathit{VL}$

$Blood =  \mathit{VB}$

$Rest =  \mathit{VRest}$

$VL =  \mathit{VLc}\cdot \mathit{BW}$

$VB =  \mathit{VBc}\cdot \mathit{BW}$

$QC =  \frac{340\cdot \mathit{BW}}{24}$

$QL =  \mathit{QLc}\cdot \mathit{QC}$

$QRest =  \mathit{QC}-\mathit{QL}$

$Htc =  \begin{cases} 0.52+\mathit{Age}\cdot 14& \text{  if  } & \mathit{Age}<0.01\\ \mathit{HtcA}\cdot (1+(0.66-\mathit{HtcA})\cdot {e}^{-(\mathit{Age}-0.01)\cdot 13.9})& {\text{  otherwise}}\end{cases}$

$BIND =  2.7\cdot 1000$

$KBIND =  0.0075\cdot 1000$

## Parameters

| id     | name                                                                    | unit          | model qualifier                            |
|:-------|:------------------------------------------------------------------------|:--------------|:-------------------------------------------|
| Age    | Age                                                                     | y             | http://purl.obolibrary.org/obo/PBPKO_00521 |
| BW     | Bodyweight                                                              | kg            | http://purl.obolibrary.org/obo/PBPKO_00008 |
| VLc    | Volume fraction of liver                                                | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00078 |
| VBc    | Volume fraction of blood                                                | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00610 |
| VL     | Volume of liver                                                         | L             | http://purl.obolibrary.org/obo/PBPKO_00077 |
| VB     | Volume of blood                                                         | L             | http://purl.obolibrary.org/obo/PBPKO_00108 |
| VRest  | Volume of rest of the body                                              | L             | http://purl.obolibrary.org/obo/PBPKO_00105 |
| QC     | Cardiac output                                                          | L/h           | http://purl.obolibrary.org/obo/PBPKO_00013 |
| QLc    | Fraction blood flow to liver                                            | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00025 |
| QL     | Blood flow to liver                                                     | L/d           | http://purl.obolibrary.org/obo/PBPKO_00025 |
| QRest  | Blood flow to rest of the body                                          | L/d           | http://purl.obolibrary.org/obo/PBPKO_00051 |
| HtcA   | Hematocrit in adulthood                                                 | dimensionless | *not specified*                            |
| Htc    | Hematocrit                                                              | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00527 |
| PL     | Partition coefficient Blood / Liver                                     | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00577 |
| PRest  | Partition coefficient Blood / Rest of the body                          | dimensionless | http://purl.obolibrary.org/obo/PBPKO_00585 |
| G      | Linear parameter for unbound lead in read cells                         | dimensionless | *not specified*                            |
| BIND   | Maximum capacity of Pb for binding by sites in red cells                | ug/L          | *not specified*                            |
| KBIND  | Half-saturation concentration of lead for binding by sites in red cells | ug/L          | *not specified*                            |
| CLiver | Concentration of chemical in liver                                      | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00539 |
| CBlood | Concentration of chemical in blood                                      | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00301 |
| CRest  | Concentration of chemical in rest of the body                           | ug/L          | http://purl.obolibrary.org/obo/PBPKO_00548 |

## Creators

*not specified*

