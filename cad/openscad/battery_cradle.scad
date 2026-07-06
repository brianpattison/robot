include <robot_params.scad>
module battery_cradle() {
  pocket=[battery_len+2*battery_padding,battery_w+2*battery_padding,battery_h/2];
  color(codex_orange)
  difference() {
    union() {
      rounded_box([pocket[0]+12,pocket[1]+12,5],6);
      translate([6,6,5]) difference(){ rounded_box([pocket[0],pocket[1],pocket[2]],5); translate([3,3,3]) rounded_box([pocket[0]-6,pocket[1]-6,pocket[2]+2],3); }
      translate([6,6,5]) cube([4,pocket[1],battery_h/2]);
      translate([pocket[0]+2,6,5]) cube([4,pocket[1],battery_h/2]);
    }
    for (x=[28,pocket[0]-18]) translate([x,(pocket[1]+12)/2,-1]) rounded_box([strap_slot_w,strap_slot_len,10],2,center=true);
    for (x=battery_cradle_mount_x) for (y=battery_cradle_mount_y)
      translate([x,y,2]) screw_hole(h=20);
    translate([pocket[0]+12,(pocket[1]+12)/2,13]) rounded_box([18,16,14],4,center=true); // wire exit
    for (y=[18,pocket[1]-6])
      translate([pocket[0]-8,y,-1]) rounded_box([5,14,10],2,center=true); // cable-tie strain relief
  }
  %translate([6+battery_padding,6+battery_padding,8]) color([0.1,0.1,0.1,0.35]) cube([battery_len,battery_w,battery_h]);
}
battery_cradle();
