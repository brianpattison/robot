include <robot_params.scad>

// Lower tub: prints open-side up with no supports. Motor pods, battery cradle,
// bumper carrier, caster, and electronics deck bolt into reinforced bosses.
module base_tray() {
  color(codex_cream)
  difference() {
    union() {
      rounded_box([base_len, base_w, base_floor_th], corner_r);
      // low side walls; interrupted for wheel wells
      translate([0,0,base_floor_th]) difference() {
        rounded_box([base_len, base_w, base_wall_h], corner_r);
        translate([wall_th,wall_th,-1]) rounded_box([base_len-2*wall_th, base_w-2*wall_th, base_wall_h+2], max(1, corner_r-wall_th));
        for (side=[-1,1]) translate([axle_x-45, side*(base_w/2-18) + base_w/2, 8]) cube([90,42,70], center=true);
      }
      // deck standoff bosses
      for (x=deck_boss_x) for (y=deck_boss_y) translate([x,y,base_floor_th]) insert_boss(d=13,h=18,hole=m3_insert_d);
      // motor pod anchor bosses
      for (x=motor_pod_anchor_x) for (y=motor_pod_anchor_y) translate([x,y,base_floor_th]) insert_boss(d=12,h=10,hole=m3_insert_d);
      // battery cradle anchor bosses; straps pass through tray windows below
      for (x=battery_cradle_mount_x) for (y=battery_cradle_mount_y)
        translate([battery_cradle_x+x,battery_cradle_y+y,base_floor_th]) insert_boss(d=12,h=8,hole=m3_insert_d);
      // rear caster reinforced pad
      translate([base_len-48, base_w/2, base_floor_th]) rounded_box([54,54,6],8,center=true);
    }
    // cable pass-throughs and lightening slots
    translate([110,base_w/2,-1]) rounded_box([54,22,base_floor_th+2],5,center=true);
    translate([205,base_w/2,-1]) rounded_box([72,18,base_floor_th+2],5,center=true);
    // battery strap windows continue the cradle slots through the tray floor
    for (x=[28,battery_len+2*battery_padding-18])
      translate([battery_cradle_x+x,battery_cradle_y+(battery_w+2*battery_padding+12)/2,-1])
        rounded_box([strap_slot_w,strap_slot_len,base_floor_th+2],2,center=true);
    // caster screw holes
    for (x=[base_len-62,base_len-34]) for (y=[base_w/2-16,base_w/2+16]) translate([x,y,base_floor_th+4]) screw_hole(h=30);
  }
}
base_tray();
