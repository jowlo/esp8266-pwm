include <lasercut/lasercut.scad>; 

thickness = 3;
x = 100;
y = 70 + 2*1.8;
z = 70; 


screw_dist_x = 83.185;
screw_offset_x = (x - screw_dist_x)/2;
screw_offset_y = 3.886 + 0.5;// - (3.823 - 3); // dist(hole, board_edge) - (dist(board_edge, usb_edge) - thickness)
screw_dist_y = 41.597;
screw_holes = [
                [1.5, screw_offset_x, screw_offset_y],
                [1.5, screw_offset_x, screw_offset_y + screw_dist_y],
                [1.5, screw_offset_x+screw_dist_x, screw_offset_y],
                [1.5, screw_offset_x+screw_dist_x, screw_offset_y + screw_dist_y]
              ];

usb_screw_offset_x = 5.334;

usb_numx = 5;
usb_numy = 2;

usb_cutouts = [ for (x = [0:usb_numx-1]) for (y = [0:usb_numy-1])
    [screw_offset_x+usb_screw_offset_x + x*15.24, (10+1.8) + y*(30 + 1.8) , 12.6, 11.3] ];


module front() {
    lasercutoutSquare(thickness=thickness, x=x, y=y,
        bumpy_finger_joints=[
                [UP, 1, 8],
                [DOWN, 1, 8],
                [LEFT, 1, 4],
                [RIGHT, 0, 4],
            ],
        cutouts = usb_cutouts
     );
    lasercutout(thickness=thickness, points = [[0,y], [0,y+thickness],
                                [-thickness, y+thickness], [-thickness, y]]);
    lasercutout(thickness=thickness, points = [[0,0], [0,-thickness],
                                [-thickness, -thickness], [-thickness, 0]]);
    lasercutout(thickness=thickness, points = [[x,0], [x,-thickness],
                                [x+thickness, -thickness], [x+thickness, 0]]);
}
color("Red",0.75)
    front();


module back() {
translate([0,0,-z - thickness]){
    lasercutoutSquare(thickness=thickness, x=x, y=y,
        bumpy_finger_joints=[
                [UP, 0, 8],
                [DOWN, 0, 8],
                [LEFT, 1, 4],
                [RIGHT, 0, 4],
            ],
        circles_remove = [
            [3, x/6, y-y/4], // antenna
            [4, x/6, y/4] // power
        ]
     );
    color("Orange",0.75)
    lasercutout(thickness=thickness, points = [[0,0], [0,-thickness],
                                [-thickness, -thickness], [-thickness, 0]]);
    lasercutout(thickness=thickness, points = [[x,0], [x,-thickness],
                                [x+thickness, -thickness], [x+thickness, 0]]);
    
    lasercutout(thickness=thickness, points = [[x,y], [x,y+thickness],
                                [x+thickness, y+thickness], [x+thickness, y]]);
}
}
color("Red",0.75)
    back();


module top() {
translate([0,y,0])
    rotate([-90,0,0]) 
    {
    lasercutoutSquare(thickness=thickness, x=x, y=z,
        finger_joints=[
                [UP, 1, 8],
                [DOWN, 1, 8],
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        circles_remove = screw_holes
    );
    lasercutout(thickness=thickness, points = [[x,0], [x,-thickness],
                                [x+thickness, -thickness], [x+thickness, 0]]);
    
    lasercutout(thickness=thickness, points = [[0,z], [0,z+thickness],
                                [-thickness, z+thickness], [-thickness, z]]);

}
}

color("Green",0.75)
    top();

color("Green",0.75)
// bottom
translate([0,0-thickness,0])
    rotate([-90,0,0]) 
    lasercutoutSquare(thickness=thickness, x=x, y=z,
        finger_joints=[
                [UP, 0, 8],
                [DOWN, 0, 8],
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        circles_remove = screw_holes        
    );
    
color("Gold",0.75)
// left
translate([-thickness,0,0])
    rotate([0,90,0]) 
    lasercutoutSquare(thickness=thickness, x=z, y=y,
        finger_joints=[
                [UP, 1, 4],
                [DOWN, 0, 4],
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ]
    );
    
color("Gold",0.75)
// right
translate([x,0,0])
    rotate([0,90,0]) 
    lasercutoutSquare(thickness=thickness, x=z, y=y,
        finger_joints=[
                [UP, 1, 4],
                [DOWN, 0, 4],
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ]
    );

module nutlock() {
    linear_extrude(height = thickness , center = false){
        difference(){
            circle(r=7);
            circle(r=5.5 / 2 / cos(180 / 6) + 0.05, $fn=6);
        }
    }
    translate([0,0,thickness])
        linear_extrude(height = thickness , center = false)
            difference(){
                circle(r=5);
                circle(r=1.5, $fn=20);
            }
}

color("Blue", 0.75)
rotate([90,0,0]) {
    translate([screw_offset_x, -screw_offset_y, thickness])
        nutlock();
    translate([x-screw_offset_x, -screw_offset_y, thickness])
        nutlock();
    translate([x-screw_offset_x, -screw_offset_y-screw_dist_y, thickness])
        nutlock();
    translate([screw_offset_x, -screw_offset_y-screw_dist_y, thickness])
        nutlock();
}

        