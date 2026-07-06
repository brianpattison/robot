include <robot_params.scad>

// First-pass removable top shell: shallow, vented service cover. Print upside
// down for support-free fit checks, or split/rework after wiring is known.
module estop_placeholder() {
  color("red") union() {
    cylinder(h=12, d=estop_mount_d);
    translate([0,0,12]) cylinder(h=14, d=estop_guard_d);
  }
}

module top_service_shell() {
  color(codex_cream)
  difference() {
    union() {
      rounded_box([base_len-54, base_w-54, 20], 14);
      translate([18,18,20]) rounded_box([base_len-90, base_w-90, 18], 10);
      // Reinforced E-stop shoulder; final hardware should add metal backing.
      translate([estop_x-27, estop_y-27, 20]) rounded_box([54,54,10], 9);
    }
    // hollow underside / service volume
    translate([8,8,-1]) rounded_box([base_len-70, base_w-70, 18], 10);
    // deck screw access holes
    for (x=deck_boss_x) for (y=deck_boss_y)
      translate([x-27,y-27,-1]) cylinder(h=50,d=12);
    // Pi cooling vents
    for (x=[70:14:140]) for (y=[65:14:135])
      translate([x,y,-1]) rounded_box([7,28,50],3);
    // speaker/status grille
    for (x=[170:13:226]) translate([x,50,-1]) rounded_box([6,58,50],3);
    // E-stop panel cutout
    translate([estop_x-27,estop_y-27,-1]) cylinder(h=60,d=estop_mount_d+2);
  }
  preview_only() {
    translate([estop_x-27,estop_y-27,31]) estop_placeholder();
    // Rear status tail LED / service badge.
    color(codex_lime) translate([base_len-86,base_w/2-27,34]) sphere(d=14);
  }
}

top_service_shell();
