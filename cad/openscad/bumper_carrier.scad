include <robot_params.scad>
module bumper_carrier() {
  color(bumper_tpu)
  difference(){
    union(){
      rounded_box([base_len+2*bumper_travel, base_w+2*bumper_travel, soft_bumper_h], corner_r+bumper_travel);
    }
    translate([bumper_travel,bumper_travel,-1]) rounded_box([base_len,base_w,soft_bumper_h+2],corner_r);
    // shallow outer groove for TPU/foam strip adhesive or captured sleeve
    translate([4,4,7]) rounded_box([base_len+2*bumper_travel-8, base_w+2*bumper_travel-8, 7], corner_r+4);
    translate([12,12,6]) rounded_box([base_len+2*bumper_travel-24, base_w+2*bumper_travel-24, 9], corner_r);
    // tray attachment holes
    for (x=[42,base_len-42]) for (y=[18,base_w-18]) translate([x+bumper_travel,y+bumper_travel,-1]) cylinder(h=40,d=m3_clearance_d);
    // rear service opening
    translate([base_len-40,base_w/2-42,-1]) cube([70,84,soft_bumper_h+2]);
  }
  preview_only() {
    // inward switch paddles that close microswitches before rigid chassis contact
    color(codex_lime) {
      for (x=[60,base_len/2,base_len-60]) translate([x+bumper_travel,bumper_travel+2,soft_bumper_h-3]) cube([22,8,12],center=true);
      for (y=[58,base_w-58]) {
        translate([bumper_travel+5,y+bumper_travel,soft_bumper_h-3]) cube([8,22,12],center=true);
        translate([base_len+bumper_travel-5,y+bumper_travel,soft_bumper_h-3]) cube([8,22,12],center=true);
      }
    }
    color(codex_lime) for (x=[42,base_len-42]) translate([x+bumper_travel,bumper_travel+2,soft_bumper_h]) cube([22,4,10],center=true);
    // simple microswitch placeholders on inner front wall and sides
    color(codex_orange) {
      for (x=[60,base_len/2,base_len-60]) translate([x+bumper_travel,bumper_travel+14,5]) cube([20,6,10],center=true);
      for (y=[58,base_w-58]) {
        translate([bumper_travel+17,y+bumper_travel,5]) cube([6,20,10],center=true);
        translate([base_len+bumper_travel-17,y+bumper_travel,5]) cube([6,20,10],center=true);
      }
    }
  }
}
bumper_carrier();
