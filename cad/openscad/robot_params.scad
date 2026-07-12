// Shared mechanical parameters for Codex house companion CAD v0.
// Units: millimeters.
$fn = 48;

// Body envelope
base_len = 300;
base_w = 220;
base_floor_th = 4;
wall_th = 3;
corner_r = 12;
base_wall_h = 34;
deck_z = 48;
total_body_h = 112;

// Personality / render colors
codex_teal = "#13C8C3";
codex_blue = "#2F6BFF";
codex_cream = "#F5F0E6";
codex_charcoal = "#242832";
codex_lime = "#B9FF66";
codex_orange = "#FF9F1C";
bumper_tpu = "#2B2F3A";

// Drive
wheel_d = 80;
wheel_w = 24;
axle_z = 42;
axle_x = 145;
wheel_clearance = 5;
motor_mount_slot = 5;
motor_pod_len = 72;
motor_pod_w = 36;
motor_pod_h = 46;

// Fasteners
m3_clearance_d = 3.4;
m3_insert_d = 4.8;
m3_insert_depth = 5.7;
m25_clearance_d = 2.8;
m2_clearance_d = 2.3;

// Electronics
pi_len = 85;
pi_w = 56;
pi_mount_x = 58;
pi_mount_y = 49;
hat_keepout_z = 28;
cooling_keepout_z = 18;
deck_th = 4;
deck_offset_x = 18;
deck_offset_y = 14;
deck_mount_x = [24, base_len-60];
deck_mount_y = [20, base_w-62];
deck_boss_x = [deck_offset_x + deck_mount_x[0], deck_offset_x + deck_mount_x[1]];
deck_boss_y = [deck_offset_y + deck_mount_y[0], deck_offset_y + deck_mount_y[1]];
deck_len = base_len - 36;
deck_w = base_w - 42;

// Battery
battery_len = 110;
battery_w = 38;
battery_h = 38;
battery_padding = 3;
strap_slot_w = 8;
strap_slot_len = 46;
battery_cradle_mount_x = [12, battery_len + 2*battery_padding + 2];
battery_cradle_mount_y = [10, battery_w + 2*battery_padding + 2];

// Storage keepout for later USB 3 module
usb_storage_len = 90;
usb_storage_w = 35;
usb_storage_h = 12;
usb_cable_bend_r = 25;

// Sensors and expression
head_z = 205;
mast_h = 120;
mast_w = 38;
mast_d = 32;
head_w = 96;
head_h = 58;
head_d = 46;
camera_board_w = 25;
camera_board_h = 24;
tof_pod_w = 24;
tof_pod_h = 18;
tof_pod_d = 18;
front_sensor_angle = 20;
bumper_travel = 8;
soft_bumper_h = 22;

// Assembly anchors / safety placeholders
battery_cradle_x = 166;
battery_cradle_y = base_w/2 - (battery_w + 2*battery_padding + 12)/2;
motor_pod_anchor_x = [axle_x-28, axle_x+28];
motor_pod_anchor_y = [base_w/2 - 61, base_w/2 + 61];
motor_pod_local_hole_x = [8, 64];
motor_pod_local_hole_y = motor_pod_w/2;
estop_x = base_len - 62;
estop_y = base_w/2;
estop_mount_d = 22;
estop_guard_d = 48;
estop_plate_w = 70;
estop_plate_d = 62;
estop_plate_th = 5;
estop_plate_mount_x = [10, estop_plate_w - 10];
estop_plate_mount_y = [10, estop_plate_d - 10];

// Split-print helpers for common 220 x 220 mm beds
base_split_x = base_len/2;
deck_split_x = deck_len/2;
seam_screw_offset = 14;
base_seam_y = [42, base_w/2, base_w-42];
deck_seam_y = [36, deck_w/2, deck_w-36];
seam_plate_w = 64;
seam_plate_d = 18;
seam_plate_th = 3;

module rounded_box(size=[10,10,10], r=2, center=false) {
  // Lightweight printable rounded rectangle prism using hull of cylinders.
  translate(center ? [-size[0]/2, -size[1]/2, -size[2]/2] : [0,0,0])
  hull() {
    for (x=[r, size[0]-r]) for (y=[r, size[1]-r])
      translate([x,y,0]) cylinder(h=size[2], r=r);
  }
}

module screw_hole(d=m3_clearance_d, h=20) {
  cylinder(h=h, d=d, center=true);
}

module preview_only() {
  if ($preview) children();
}

module insert_boss(d=10, h=8, hole=m3_insert_d) {
  difference() { cylinder(h=h, d=d); translate([0,0,-1]) cylinder(h=h+2, d=hole); }
}
