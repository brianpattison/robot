include <robot_params.scad>
use <base_tray.scad>
use <electronics_deck.scad>
use <bumper_carrier.scad>

// Select one output with:
// openscad -D 'split_part="base_front"' -o cad/exports/stl/base_front.stl cad/openscad/split_print_variants.scad
split_part = "layout";

module base_seam_holes(x) {
  for (y=base_seam_y)
    translate([x,y,base_floor_th/2]) screw_hole(h=20);
}

module deck_seam_holes(x) {
  for (y=deck_seam_y)
    translate([x,y,deck_th/2]) screw_hole(h=20);
}

module base_tray_front_split() {
  difference() {
    intersection() {
      base_tray();
      translate([-1,-1,-1]) cube([base_split_x+1,base_w+2,total_body_h]);
    }
    base_seam_holes(base_split_x-seam_screw_offset);
  }
}

module base_tray_rear_split() {
  difference() {
    intersection() {
      base_tray();
      translate([base_split_x,-1,-1]) cube([base_len-base_split_x+1,base_w+2,total_body_h]);
    }
    base_seam_holes(base_split_x+seam_screw_offset);
  }
}

module seam_plate() {
  difference() {
    rounded_box([seam_plate_w,seam_plate_d,seam_plate_th],3);
    for (x=[seam_plate_w/2-seam_screw_offset,seam_plate_w/2+seam_screw_offset])
      translate([x,seam_plate_d/2,seam_plate_th/2]) screw_hole(h=20);
  }
}

module electronics_deck_left_split() {
  difference() {
    intersection() {
      electronics_deck();
      translate([-1,-1,-1]) cube([deck_split_x+1,deck_w+2,deck_th+20]);
    }
    deck_seam_holes(deck_split_x-seam_screw_offset);
  }
}

module electronics_deck_right_split() {
  difference() {
    intersection() {
      electronics_deck();
      translate([deck_split_x,-1,-1]) cube([deck_len-deck_split_x+1,deck_w+2,deck_th+20]);
    }
    deck_seam_holes(deck_split_x+seam_screw_offset);
  }
}

module bumper_quadrant(x_index=0, y_index=0) {
  bumper_len = base_len + 2*bumper_travel;
  bumper_w = base_w + 2*bumper_travel;
  x0 = x_index == 0 ? 0 : bumper_len/2;
  y0 = y_index == 0 ? 0 : bumper_w/2;
  intersection() {
    bumper_carrier();
    translate([x0,y0,-1]) cube([bumper_len/2+1,bumper_w/2+1,soft_bumper_h+4]);
  }
}

module split_layout_preview() {
  base_tray_front_split();
  translate([170,0,0]) base_tray_rear_split();
  for (i=[0:2]) translate([75,base_w+28+i*28,0]) seam_plate();

  translate([0,base_w+130,0]) electronics_deck_left_split();
  translate([160,base_w+130,0]) electronics_deck_right_split();
  for (i=[0:2]) translate([330,base_w+140+i*28,0]) seam_plate();

  translate([380,0,0]) bumper_quadrant(0,0);
  translate([540,0,0]) bumper_quadrant(1,0);
  translate([380,140,0]) bumper_quadrant(0,1);
  translate([540,140,0]) bumper_quadrant(1,1);
}

if (split_part == "base_front") base_tray_front_split();
else if (split_part == "base_rear") base_tray_rear_split();
else if (split_part == "base_seam_plate") seam_plate();
else if (split_part == "deck_left") electronics_deck_left_split();
else if (split_part == "deck_right") electronics_deck_right_split();
else if (split_part == "deck_seam_plate") seam_plate();
else if (split_part == "bumper_front_left") bumper_quadrant(0,0);
else if (split_part == "bumper_rear_left") bumper_quadrant(1,0);
else if (split_part == "bumper_front_right") bumper_quadrant(0,1);
else if (split_part == "bumper_rear_right") bumper_quadrant(1,1);
else split_layout_preview();
