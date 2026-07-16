# Retail Sourcing Policy And Audit

Date: 2026-07-12

The robot should be reproducible by a home builder in the United States without
calling a sales engineer or hiring a machine shop. A purchased production part
passes this policy when it has:

- A normal US online checkout with quantity one available.
- A stable manufacturer part number and primary technical documentation.
- No required custom machining, sheet-metal fabrication, or PCB fabrication.
- A reasonable expectation of restocking rather than a one-off marketplace listing.
- Preferably a second US source when it affects motion, battery power, charging, or physical stopping.

Mainstream specialist sellers such as DigiKey, Mouser, Pololu, Adafruit,
SparkFun, McMaster-Carr, and established US automotive or marine retailers
count as retail sources. Printed parts, cut wire, crimped harnesses, heat-shrink,
and ordinary assembly operations are expected. Marketplace listings can be a
backup source but should not be the only source for safety-critical hardware.

## Implemented Retail-Only Contract

| Legacy plan | D024 disposition | Implemented replacement |
| --- | --- | --- |
| Albright SW60/custom carrier and later Cole Hersee 24117 candidate | Rejected: custom support and unresolved packaging | Panasonic CB1A-R-M-12V sealed automotive SPST-NO relay with integral bracket, one 5.4 mm mounting hole, 40 A contacts at 14 V, 12 V/134 mA coil, and built-in resistor. |
| Custom four-branch Nano2/Micro-Fit PCB | Rejected: custom PCB fabrication | Blue Sea Systems 5045 complete covered four-circuit ATO/ATC fuse block, 92.5 x 43.8 x 32.5 mm, with two mounting holes on 65.1 mm centers. |
| 64.5 mm machined shaft, DIN 471 ring, and custom-length spacers | Rejected: precision machining and cut-to-length metal | WDS 615-M6-8-65 shoulder bolt per side with an M6 washer, prevailing-torque locknut, and stock goBILDA spacers/shim. |
| Protected rear UART PCB and service jack | Rejected: custom PCB for a nonessential interface | Blank center rear cartridge. Service the robot internally with motor power physically isolated. |
| Webbing handles and custom metal clamp plates | Rejected: custom load-bearing metal | No carry handles. Power down and lift with two hands under the tray. |

## Motor Cutoff

The **Panasonic CB1A-R-M-12V** is the implemented mechanical baseline. Its
integral metal bracket uses one 5.4 mm mounting hole; the sealed normally-open
relay is rated 40 A at 14 V DC and uses a 12 V, 134 mA coil with a built-in
resistor. The printed deck locates the retail assembly but does not replace its
metal bracket or carry terminal loads.

Release still requires delivered-part identity and fit, appropriately sized
conductors and 6.3 mm terminals, strain relief, contact/coil polarity review,
driver sizing, proof that the built-in resistor is the intended suppression,
dropout timing, temperature rise, fault behavior, and fail-stopped E-stop tests.
The E-stop's two direct-opening NC channels remain in the low-current
fail-deenergized enable path; the relay does not make the E-stop optional.

## Accessory Distribution

The **Blue Sea Systems 5045** is the implemented accessory-distribution
baseline. It is a complete retail four-circuit ATO/ATC block with insulating
cover and labels, modeled at 92.5 x 43.8 x 32.5 mm with two mounting holes on
65.1 mm centers. Keep the prototype limits at 6 A total and 5 A on any branch,
even though the purchased block has higher catalog ratings.

Release requires a battery-near accessory feeder fuse, branch fuses selected
from measured loads and conductor ampacity, covered live parts, keyed polarity,
terminal protection, strain relief, durable labels, power-off-only fuse
service, selective far-end short tests, all-branch thermal soak, vibration/tug
testing, and proof that no accessory path bypasses the independently fused and
relay-cut motor branch.

## Front Idler And Handling

Each front support uses a **WDS 615-M6-8-65** shoulder bolt with a 65 mm-long,
8 mm shoulder and M6 thread, two 608 bearings, an M6 washer, a prevailing-
torque locknut, and stock goBILDA spacers/shim. Plastic locates the bearings;
the purchased metal stack provides retention. Qualify bearing support, thread
engagement, spacer stack, axial play, wheel alignment, locknut retention, and
loaded skid turns before household motion.

The MVP has no carry handles or custom load-bearing metal. Shut down, isolate
motor power, and lift with two hands under the tray. Do not lift by the shell,
lid, head, bumper, fairings, wiring, or rear cartridges.

## Rear Interface

The 126 x 58 mm frame keeps three removable cartridges: charge-only at rear
left, blank at center, and physical mute at rear right. The blank cartridge has
no jack, PCB, wiring, or service-mode promise. Internal diagnostics require the
robot to be powered down or the motor branch to be physically isolated.

## Historical Decisions

D024 supersedes D018, D021, and D023 for production sourcing and replaces the
intermediate cutoff candidate recorded in D024. Those entries remain in the
decision log so the rejected constraints and safety reasoning are not lost.
