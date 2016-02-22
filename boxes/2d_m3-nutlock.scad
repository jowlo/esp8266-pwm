module foot2d() {
    difference(){
        circle(r=7, $fn=60);
        circle(r=5.5 / 2 / cos(180 / 6) + 0.05, $fn=6);
    }
    translate([0,13])
            difference(){
                circle(r=5, $fn=60);
                circle(r=1.5, $fn=20);
            }
    translate([0,22])
            difference(){
                circle(r=3, $fn=60);
                circle(r=1.5, $fn=20);
            }
}

module foot(thickness) {
    linear_extrude(height = thickness , center = false){
        difference(){
            circle(r=7, $fn=60);
            circle(r=5.5 / 2 / cos(180 / 6) + 0.05, $fn=6);
        }
    }
    translate([0,0,thickness])
        linear_extrude(height = thickness , center = false){
            difference(){
                circle(r=5, $fn=60);
                circle(r=1.5, $fn=20);
            }
        }
}

//foot2d();
//foot(3);