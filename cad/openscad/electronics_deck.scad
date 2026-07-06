include <robot_params.scad>

module electronics_deck() {
  color(codex_teal)
  difference() {
    union() {
      rounded_box([deck_len, deck_w, deck_th], 10);
      // Pi standoffs
      pi_x=42; pi_y=44;
      for (x=[pi_x, pi_x+pi_mount_x]) for (y=[pi_y, pi_y+pi_mount_y]) translate([x,y,deck_th]) insert_boss(d=8,h=7,hole=m25_clearance_d);
      // generic regulator/controller standoffs
      for (x=[150,185,220]) for (y=[46,86,126]) translate([x,y,deck_th]) insert_boss(d=8,h=6,hole=m3_insert_d);
      // E-stop mount plate standoffs, aligned to the global shell cutout
      for (x=estop_plate_mount_x) for (y=estop_plate_mount_y)
        translate([estop_x-deck_offset_x-estop_plate_w/2+x,estop_y-deck_offset_y-estop_plate_d/2+y,deck_th])
          insert_boss(d=10,h=8,hole=m3_insert_d);
    }
    // mount holes to base tray
    for (x=deck_mount_x) for (y=deck_mount_y) translate([x,y,0]) screw_hole(h=20);
    // vents around Pi and HAT keepout
    for (x=[46:12:100]) for (y=[118:12:146]) translate([x,y,-1]) rounded_box([7,28,deck_th+2],3);
    // zip tie slots / wire channels
    for (x=[120,170,220]) for (y=[24,base_w-72]) translate([x,y,-1]) rounded_box([24,5,deck_th+2],2);
    translate([122,96,-1]) rounded_box([82,12,deck_th+2],3);
  }
  // transparent future HAT/cooling envelope for preview only
  %translate([42,44,deck_th+7]) color([0.2,0.45,1,0.22]) cube([pi_len,pi_w,hat_keepout_z+cooling_keepout_z]);
}
electronics_deck();
