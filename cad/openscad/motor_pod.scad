include <robot_params.scad>
module motor_pod(side=1) {
  color(codex_charcoal)
  difference(){
    union(){
      rounded_box([motor_pod_len,motor_pod_w,motor_pod_h],5);
      translate([8,motor_pod_w/2,motor_pod_h/2]) rotate([0,90,0]) cylinder(h=10,d=42,center=true);
      for (x=[12,motor_pod_len-12]) translate([x,0,0]) cube([10,motor_pod_w,8]);
      for (x=[18,motor_pod_len-18]) translate([x,motor_pod_w/2,8]) cylinder(h=motor_pod_h-8,d1=12,d2=8);
    }
    translate([8,motor_pod_w/2,motor_pod_h/2]) rotate([0,90,0]) cylinder(h=30,d=25,center=true);
    for (x=[20,motor_pod_len-20]) for (z=[17,31]) translate([x,motor_pod_w/2,z]) rotate([90,0,0]) hull(){ cylinder(h=50,d=m3_clearance_d,center=true); translate([motor_mount_slot,0,0]) cylinder(h=50,d=m3_clearance_d,center=true); }
    for (x=motor_pod_local_hole_x) translate([x,motor_pod_local_hole_y,4]) screw_hole(h=20);
  }
  %translate([8, side*(motor_pod_w/2+wheel_w/2+wheel_clearance), axle_z-motor_pod_h/2]) rotate([90,0,0]) color([0.05,0.05,0.05,0.35]) cylinder(h=wheel_w,d=wheel_d,center=true);
}
motor_pod();
