include <robot_params.scad>

// Reinforced E-stop mount concept. The top shell provides access; this plate
// ties the switch body back to deck standoffs and gives motor-cut wiring relief.
module estop_mount_plate(show_cap=true) {
  color(codex_charcoal)
  difference() {
    union() {
      rounded_box([estop_plate_w, estop_plate_d, estop_plate_th], 7);
      translate([estop_plate_w/2,estop_plate_d/2,estop_plate_th])
        cylinder(h=4, d=estop_guard_d+8);
      translate([estop_plate_w-18,estop_plate_d/2-18,estop_plate_th])
        rounded_box([12,36,8],4);
    }
    translate([estop_plate_w/2,estop_plate_d/2,-1])
      cylinder(h=estop_plate_th+8,d=estop_mount_d+2);
    translate([estop_plate_w/2+estop_mount_d/2+5,estop_plate_d/2,-1])
      rounded_box([9,4,estop_plate_th+10],1,center=true); // anti-rotation notch placeholder
    for (x=estop_plate_mount_x) for (y=estop_plate_mount_y)
      translate([x,y,estop_plate_th/2]) screw_hole(h=20);
    for (y=[estop_plate_d/2-11,estop_plate_d/2+11])
      translate([estop_plate_w-12,y,-1]) rounded_box([6,14,estop_plate_th+10],2,center=true);
  }

  if (show_cap)
    preview_only()
      translate([estop_plate_w/2,estop_plate_d/2,estop_plate_th+4])
        estop_preview_cap();
}

module estop_preview_cap() {
  color("red") union() {
    cylinder(h=12, d=estop_mount_d);
    translate([0,0,12]) cylinder(h=14, d=estop_guard_d);
  }
}

estop_mount_plate();
