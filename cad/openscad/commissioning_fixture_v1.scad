// RB-FIXTURE-V1: one support-free PETG plate for unpowered commissioning.
// Print exactly as modeled: component face at Z=0, hollow feet upward. Flip for use.

include <generated/commissioning_fixture_v1_data.scad>

$fn = 48;
epsilon = 0.1;
foot_outer = 24;
foot_wall = 2.4;
rib_width = 4;
rib_height = 8;

module rounded_slot(length, width, height) {
    hull() {
        translate([-(length - width) / 2, 0, 0]) cylinder(d=width, h=height);
        translate([(length - width) / 2, 0, 0]) cylinder(d=width, h=height);
    }
}

module hollow_foot(x, y) {
    difference() {
        translate([x - foot_outer / 2, y - foot_outer / 2, plate_thickness])
            cube([foot_outer, foot_outer, foot_height]);
        translate([
            x - foot_outer / 2 + foot_wall,
            y - foot_outer / 2 + foot_wall,
            plate_thickness - epsilon
        ])
            cube([
                foot_outer - 2 * foot_wall,
                foot_outer - 2 * foot_wall,
                foot_height + 2 * epsilon
            ]);
    }
}

module underside_ribs() {
    inset = 15;
    translate([-plate_width / 2 + inset, -plate_depth / 2 + inset, plate_thickness])
        cube([plate_width - 2 * inset, rib_width, rib_height]);
    translate([-plate_width / 2 + inset, plate_depth / 2 - inset - rib_width, plate_thickness])
        cube([plate_width - 2 * inset, rib_width, rib_height]);
    translate([-plate_width / 2 + inset, -plate_depth / 2 + inset, plate_thickness])
        cube([rib_width, plate_depth - 2 * inset, rib_height]);
    translate([plate_width / 2 - inset - rib_width, -plate_depth / 2 + inset, plate_thickness])
        cube([rib_width, plate_depth - 2 * inset, rib_height]);
}

module fixture_blank() {
    union() {
        translate([-plate_width / 2, -plate_depth / 2, 0])
            cube([plate_width, plate_depth, plate_thickness]);
        for (x = [-plate_width / 2 + 15, plate_width / 2 - 15])
            for (y = [-plate_depth / 2 + 15, plate_depth / 2 - 15])
                hollow_foot(x, y);
        underside_ribs();
    }
}

module through_holes() {
    hole_height = plate_thickness + 2 * epsilon;
    translate([estop_center[0], estop_center[1], -epsilon])
        cylinder(d=estop_hole_diameter, h=hole_height);
    translate([lamp_center[0], lamp_center[1], -epsilon])
        cylinder(d=lamp_hole_diameter, h=hole_height);

    for (center = bumper_centers)
        for (offset = [-bumper_hole_spacing / 2, bumper_hole_spacing / 2])
            translate([center[0] + offset, center[1], -epsilon])
                cylinder(d=3.4, h=hole_height);

    for (center = [driver_tie_center, relay_tie_center])
        for (offset = [-15, 15])
            translate([center[0] + offset, center[1], -epsilon])
                rotate([0, 0, 90]) rounded_slot(12, 3.2, hole_height);

    // Two cable-management stations beside the breadboard.
    for (y = [20, 76])
        translate([-106, y, -epsilon]) rounded_slot(14, 3.2, hole_height);
}

difference() {
    fixture_blank();
    through_holes();
}
