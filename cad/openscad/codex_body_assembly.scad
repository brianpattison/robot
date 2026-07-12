include <robot_params.scad>
use <base_tray.scad>
use <electronics_deck.scad>
use <battery_cradle.scad>
use <motor_pod.scad>
use <bumper_carrier.scad>
use <tof_sensor_pod.scad>
use <camera_head_bracket.scad>
use <top_service_shell.scad>
use <estop_mount_plate.scad>

module placed_tof(x, y, z, heading=180) {
  translate([x,y,z]) rotate([0,0,heading+90]) tof_sensor_pod(0);
}

// Color preview assembly. Generated meshes remain outputs; source stays here.
base_tray();
translate([-bumper_travel,-bumper_travel,8]) bumper_carrier();
translate([deck_offset_x,deck_offset_y,deck_z]) electronics_deck();
translate([battery_cradle_x,battery_cradle_y,base_floor_th+1]) battery_cradle();
translate([motor_pod_anchor_x[0]-motor_pod_local_hole_x[0], motor_pod_anchor_y[1]-motor_pod_local_hole_y, 6]) motor_pod(1);
translate([motor_pod_anchor_x[0]-motor_pod_local_hole_x[0], motor_pod_anchor_y[0]-motor_pod_local_hole_y, 6]) motor_pod(-1);
for (side=[-1,1]) translate([axle_x, base_w/2 + side*(base_w/2+wheel_w/2+wheel_clearance), axle_z]) rotate([90,0,0]) color("#111111") cylinder(h=wheel_w,d=wheel_d,center=true);
placed_tof(28,base_w/2,42,180);
placed_tof(56,34,42,180+front_sensor_angle);
placed_tof(56,base_w-34,42,180-front_sensor_angle);
placed_tof(base_len/2,18,42,-90);
placed_tof(base_len/2,base_w-18,42,90);
translate([72,base_w/2-mast_d/2,base_floor_th+base_wall_h]) camera_head_bracket();
translate([estop_x-estop_plate_w/2,estop_y-estop_plate_d/2,deck_z+deck_th+14]) estop_mount_plate(false);
translate([27,27,86]) top_service_shell();
