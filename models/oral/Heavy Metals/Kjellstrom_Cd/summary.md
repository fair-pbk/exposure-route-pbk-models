# Kjellstrom1978_Cd_Human

## Overview

| key                          | value                                         |
|:-----------------------------|:----------------------------------------------|
| Modelled species/orgamism(s) | http://purl.obolibrary.org/obo/NCBITaxon_9606 |
| Model chemical(s)            | http://purl.obolibrary.org/obo/CHEBI_22977    |
| Input route(s)               | 1 (oral)                                      |
| Time resolution              | d                                             |
| Amounts unit                 | ug                                            |
| Volume unit                  | L                                             |
| Number of compartments       | 9                                             |
| Number of species            | 9                                             |
| Number of parameters         | 15 (15 external / 0 internal)                 |

## Diagram

![Diagram](summary.svg)

## Compartments

| id                | name              | unit   | model qualifier                            |
|:------------------|:------------------|:-------|:-------------------------------------------|
| GI                | Gut Intestine     | L      | http://purl.obolibrary.org/obo/PBPKO_00478 |
| Intestinal_Tissue | Intestinal tissue | L      | http://purl.obolibrary.org/obo/PBPKO_00477 |
| Liver             | Liver             | L      | http://purl.obolibrary.org/obo/PBPKO_00558 |
| Kidney            | Kidney            | L      | http://purl.obolibrary.org/obo/PBPKO_00557 |
| Plasma            | Plasma            | L      | http://purl.obolibrary.org/obo/PBPKO_00488 |
| Red_Blood_Cell    | Red blood cell    | L      | http://purl.obolibrary.org/obo/PBPKO_00634 |
| Metallothionein   | Metallothionein   | L      | *not specified*                            |
| Rest              | Rest of the body  | L      | http://purl.obolibrary.org/obo/PBPKO_00450 |
| Daily_Uptake      | Daily uptake      | L      | *not specified*                            |

## Species

| id               | name                                    | unit   | model qualifier                            |
|:-----------------|:----------------------------------------|:-------|:-------------------------------------------|
| AGI              | Amount of chemical in gut intestine     | ug     | http://purl.obolibrary.org/obo/PBPKO_00496 |
| ATI              | Amount of chemical in intestinal tissue | ug     | *not specified*                            |
| ALiver           | Amount of chemical in liver             | ug     | http://purl.obolibrary.org/obo/PBPKO_00497 |
| AKidney          | Amount of chemical in kidney            | ug     | http://purl.obolibrary.org/obo/PBPKO_00498 |
| APlasma          | Amount of chemical in plasma            | ug     | http://purl.obolibrary.org/obo/PBPKO_00502 |
| ARBC             | Amount of chemical in red blood cells   | ug     | *not specified*                            |
| AMetallothionein | Amount of chemical in metallothionein   | ug     | *not specified*                            |
| ARest            | Amount of chemical in the rest of body  | ug     | http://purl.obolibrary.org/obo/PBPKO_00501 |
| ADaily_Uptake    | Amount of chemical daily uptaken        | ug     | *not specified*                            |

## Transfer equations

| id   | from             | to               | equation                                                                                                                                                                                                                           |
|:-----|:-----------------|:-----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _J0  | AGI              | ATI              | $ \mathit{C5}\cdot \mathit{AGI}$                                                                                                                                                                                                   |
| _J1  | ATI              | ADaily_Uptake    | $ \mathit{C6}\cdot \mathit{ATI}$                                                                                                                                                                                                   |
| _J2  | ADaily_Uptake    | AMetallothionein | $ \begin{cases} \mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{C8}& {\text{  otherwise}}\end{cases}$                                                   |
| _J3  | ADaily_Uptake    | APlasma          | $ \begin{cases} \mathit{ADaily_{Uptake}}-\mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{ADaily_{Uptake}}-\mathit{C8}& {\text{  otherwise}}\end{cases}$ |
| _J4  | APlasma          | ARest            | $ \mathit{C9}\cdot \mathit{APlasma}$                                                                                                                                                                                               |
| _J5  | ARest            | APlasma          | $ \mathit{C10}\cdot \mathit{ARest}$                                                                                                                                                                                                |
| _J6  | APlasma          | ALiver           | $ \mathit{C12}\cdot \mathit{APlasma}$                                                                                                                                                                                              |
| _J7  | ALiver           | APlasma          | $ \mathit{C13}\cdot \mathit{ALiver}$                                                                                                                                                                                               |
| _J8  | ALiver           | AMetallothionein | $ \mathit{C14}\cdot \mathit{ALiver}$                                                                                                                                                                                               |
| _J9  | ARBC             | AMetallothionein | $ \mathit{C16}\cdot \mathit{ARBC}$                                                                                                                                                                                                 |
| _J10 | AMetallothionein | AKidney          | $ \mathit{C17}\cdot \mathit{AMetallothionein}$                                                                                                                                                                                     |
| _J11 | AKidney          | APlasma          | $ \mathit{C18}\cdot \mathit{AKidney}$                                                                                                                                                                                              |
| _J12 | APlasma          | ARBC             | $ \mathit{CX}\cdot \mathit{APlasma}$                                                                                                                                                                                               |

## ODEs

$\frac{d[\mathtt{AGI}]}{dt} = -  \mathit{C5}\cdot \mathit{AGI}$

$\frac{d[\mathtt{ATI}]}{dt} =  \mathit{C5}\cdot \mathit{AGI}
            -  \mathit{C6}\cdot \mathit{ATI}$

$\frac{d[\mathtt{ALiver}]}{dt} =  \mathit{C12}\cdot \mathit{APlasma}
               -  \mathit{C13}\cdot \mathit{ALiver}
               -  \mathit{C14}\cdot \mathit{ALiver}$

$\frac{d[\mathtt{AKidney}]}{dt} =  \mathit{C17}\cdot \mathit{AMetallothionein}
                -  \mathit{C18}\cdot \mathit{AKidney}$

$\frac{d[\mathtt{APlasma}]}{dt} =  \begin{cases} \mathit{ADaily_{Uptake}}-\mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{ADaily_{Uptake}}-\mathit{C8}& {\text{  otherwise}}\end{cases}
                -  \mathit{C9}\cdot \mathit{APlasma}
                +  \mathit{C10}\cdot \mathit{ARest}
                -  \mathit{C12}\cdot \mathit{APlasma}
                +  \mathit{C13}\cdot \mathit{ALiver}
                +  \mathit{C18}\cdot \mathit{AKidney}
                -  \mathit{CX}\cdot \mathit{APlasma}$

$\frac{d[\mathtt{ARBC}]}{dt} = -  \mathit{C16}\cdot \mathit{ARBC}
             +  \mathit{CX}\cdot \mathit{APlasma}$

$\frac{d[\mathtt{AMetallothionein}]}{dt} =  \begin{cases} \mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{C8}& {\text{  otherwise}}\end{cases}
                         +  \mathit{C14}\cdot \mathit{ALiver}
                         +  \mathit{C16}\cdot \mathit{ARBC}
                         -  \mathit{C17}\cdot \mathit{AMetallothionein}$

$\frac{d[\mathtt{ARest}]}{dt} =  \mathit{C9}\cdot \mathit{APlasma}
              -  \mathit{C10}\cdot \mathit{ARest}$

$\frac{d[\mathtt{ADaily-Uptake}]}{dt} =  \mathit{C6}\cdot \mathit{ATI}
                      -  \begin{cases} \mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{C8}& {\text{  otherwise}}\end{cases}
                      -  \begin{cases} \mathit{ADaily_{Uptake}}-\mathit{C7}\cdot \mathit{ADaily_{Uptake}}& \text{  if  } & \mathit{C7}\cdot \mathit{ADaily_{Uptake}}<\mathit{C8}\\ \mathit{ADaily_{Uptake}}-\mathit{C8}& {\text{  otherwise}}\end{cases}$

## Initial assignments

$C17 =  \begin{cases} 0.95& \text{  if  } & \mathit{Age}<30\\ \frac{0.95\cdot 0.33\cdot (\mathit{Age}-30)}{80-30}& {\text{  otherwise}}\end{cases}$

## Parameters

| id   | name                                            | unit   | model qualifier                            |
|:-----|:------------------------------------------------|:-------|:-------------------------------------------|
| Age  | Age                                             | y      | http://purl.obolibrary.org/obo/PBPKO_00521 |
| BW   | Bodyweight                                      | kg     | http://purl.obolibrary.org/obo/PBPKO_00008 |
| C5   | Daily intake retained in the intestinal walls   | /d     | *not specified*                            |
| C6   | Coefficient of absorption                       | /d     | http://purl.obolibrary.org/obo/PBPKO_00142 |
| C7   | Fraction from daily uptake to metallothionein   | /d     | *not specified*                            |
| C8   | Maximum amount in metallothionein               | ug/d   | *not specified*                            |
| C9   | Fraction from plasma to rest of the body        | /d     | *not specified*                            |
| C10  | Fraction from rest of the body to plasma        | /d     | *not specified*                            |
| C12  | Fraction from plasma to liver                   | /d     | *not specified*                            |
| C13  | Fraction from liver to plasma                   | /d     | *not specified*                            |
| C14  | Fraction from liver to metallothionein          | /d     | *not specified*                            |
| C16  | Fraction from red blood cell to metallothionein | /d     | *not specified*                            |
| C17  | Fraction from metallothionein to kidney         | /d     | *not specified*                            |
| C18  | Fraction from kidney to plasma                  | /d     | *not specified*                            |
| CX   | Fraction from plasma to red blood cell          | /d     | *not specified*                            |

## Creators

*not specified*

