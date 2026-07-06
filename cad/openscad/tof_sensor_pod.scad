include <robot_params.scad>
tof_variant = "straight";

module tof_sensor_pod(angle=0) {
  rotate([0,0,angle]) color(codex_blue) difference(){
    union(){ rounded_box([tof_pod_w,tof_pod_d,tof_pod_h],3); translate([0,-5,tof_pod_h-5]) cube([tof_pod_w,8,5]); }
    translate([tof_pod_w/2,-1,tof_pod_h/2]) rotate([90,0,0]) cylinder(h=10,d=10,center=true);
    for (x=[5,tof_pod_w-5]) translate([x,tof_pod_d/2,tof_pod_h/2]) rotate([90,0,0]) screw_hole(d=m2_clearance_d,h=20);
  }
}

if (tof_variant == "left") tof_sensor_pod(front_sensor_angle);
else if (tof_variant == "right") tof_sensor_pod(-front_sensor_angle);
else if (tof_variant == "layout") {
  tof_sensor_pod();
  translate([34,0,0]) tof_sensor_pod(front_sensor_angle);
  translate([68,0,0]) tof_sensor_pod(-front_sensor_angle);
}
else tof_sensor_pod();
