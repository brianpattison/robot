include <robot_params.scad>
module camera_head_bracket() {
  color(codex_teal) difference(){
    union(){
      rounded_box([mast_w,mast_d,mast_h],6);
      translate([-(head_w-mast_w)/2,-7,mast_h-6]) rounded_box([head_w,head_d,head_h],12);
    }
    translate([mast_w/2,-12,mast_h+22]) rotate([90,0,0]) cylinder(h=20,d=15,center=true); // camera lens
    translate([(mast_w-camera_board_w)/2,-9,mast_h+10]) cube([camera_board_w,4,camera_board_h]);
    translate([mast_w/2-7,mast_d/2-1,16]) rounded_box([14,8,mast_h-28],3); // ribbon path
    for (x=[7,mast_w-7]) for (y=[7,mast_d-7]) translate([x,y,0]) screw_hole(h=20);
  }
  preview_only() {
    // brow / ears and eyes for friendly Codex look; final faceplate is separate.
    translate([-head_w/2+8,-10,mast_h+head_h-8]) rotate([0,18,0]) color(codex_blue) rounded_box([34,12,10],5);
    translate([head_w/2-42,-10,mast_h+head_h-8]) rotate([0,-18,0]) color(codex_blue) rounded_box([34,12,10],5);
    color(codex_lime) translate([mast_w/2-28,-14,mast_h+34]) sphere(d=10);
    color(codex_lime) translate([mast_w/2+28,-14,mast_h+34]) sphere(d=10);
  }
}
camera_head_bracket();
