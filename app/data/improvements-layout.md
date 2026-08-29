# Description of Improvements: what the template cannot say

The layout lives in `app/templates/Improvements.docx`. Open it in Word to
change a heading, a label, or the order. This file holds only the facts a Word
file cannot carry: where each value comes from, and which fields are optional.

Measured 2026-08-28 against the Blaul Lofts job, which is the only job in the
vault holding both an assessor card and an inspection transcript for this
section: `Report Examples/BURLINGTON_425 Valley St, (Blaul Lofts)`.

## Where each value comes from

`card` is the assessor's property record card. `transcript` is the recording of
Mark's walkthrough. `mark` is his judgment and the app never fills it. `none`
means neither source carries it, so it stays blank and says so.

| Field | Source |
|---|---|
| Foundation | card + transcript |
| Exterior Walls | card + transcript |
| Roof | card |
| Windows | card |
| Walls | card + transcript |
| Ceilings | none |
| Floors | transcript |
| Kitchens | transcript |
| Bathrooms | transcript |
| HVAC | transcript |
| Electrical Service | transcript |
| Common Area | transcript |
| Parking | none |
| Trash Removal | transcript |
| Plantings | transcript |
| Sidewalks | transcript |

## Optional fields

These appear only when the job has them. They are not missing when absent.

| Field | Block | Source |
|---|---|---|
| Store Fronts | BUILDING EXTERIOR | none |
| Lighting | BUILDING INTERIOR | none |
| Amenities | BUILDING INTERIOR | transcript |
| Fitness Center | BUILDING INTERIOR | transcript |

## The repeating block

`BUILDING INTERIOR – [NAME]` repeats once per tenancy, per building, or per
use. Blaul uses three: Common Areas, Commercial Suite, Apartment Units. St John
Vianney splits the same way per building: Church, Rectory.

## Numbers the app works out for itself

Mark's Excel tool used to push these into Word. It no longer does, so they are
ours. Each one names what it is made from.

| Value | How |
|---|---|
| Land to building ratio | card land area / card gross building area |
| Actual age | year of value - card year built |
| Total building area | card gross building area |

## Never filled by the app

Effective age. Remaining economic life. Condition. Quality. Every sentence in
GENERAL and CONCLUSION. These are Mark's opinion and a wrong one reaches his
client over his signature.

## Known to be outside both sources

Measured on Blaul. The document carried these and neither the card nor the
transcript holds them, so the app cannot produce them and must not try: the
building's history and former name, the renovation year, leased parking
counts, and the marketing list of amenities.
