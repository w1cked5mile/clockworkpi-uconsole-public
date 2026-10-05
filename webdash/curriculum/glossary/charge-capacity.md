---
id: charge-capacity
term: Charge (%)
tooltip: The PMIC's fuel-gauge estimate of remaining charge.
good_bad: Rough until the gauge has seen a full charge and discharge.
try_this: Note the percentage before and after a battery lab.
learn_more: '#/learn/m/M1'
---

Combines voltage with a count of charge in and out; how it is configured on this AXP228 is
unverified. A reading that does not depend on the gauge's state-of-charge model is the pack
voltage itself, from `upower -i $(upower -e | grep -i battery)`; the estimate only firms up once
the gauge has seen one full charge and discharge.
