include <lasercut/lasercut.scad>; 


thickness = 4;
pcb = 1.6;
x = 40;
y = 35;
z = 60; 

//usb_cutout = [ 12.6, 11.3] ];

screw_dist_x = 22.860;
screw_offset_x = (x - screw_dist_x)/2;
screw_offset_y = 4.546 + 0.5;// - (3.823 - 3); // dist(hole, board_edge) - (dist(board_edge, usb_edge) - thickness)
screw_dist_y = 40.64;
screw_holes = [
                [1.5, screw_offset_x, screw_offset_y],
                [1.5, screw_offset_x, screw_offset_y + screw_dist_y],
                [1.5, screw_offset_x+screw_dist_x, screw_offset_y],
                [1.5, screw_offset_x+screw_dist_x, screw_offset_y + screw_dist_y]
              ];

module front() {
    union() {
        lasercutoutSquare(thickness=thickness, x=x, y=y,
            bumpy_finger_joints=[
                    [UP, 1, 4],
                    [DOWN, 1, 4],
                    [LEFT, 1, 4],
                    [RIGHT, 0, 4],
                ],
            cutouts = [[x/2-12.6/2,2+pcb+thickness, 12.6, 11.3]]
        );
    }
}
color("Orange",0.75)
    front();

module back() {
translate([0,0,-z - thickness]){
    union() {
        lasercutoutSquare(thickness=thickness, x=x, y=y,
            bumpy_finger_joints=[
                    [UP, 0, 4],
                    [DOWN, 0, 4],
                    [LEFT, 1, 4],
                    [RIGHT, 0, 4],
                ]
        );
    }
}
}
color("Cyan",0.75)
    back();


module top() {
translate([0,y,0])
    rotate([-90,0,0]) {
        union() {
            lasercutoutSquare(thickness=thickness, x=x, y=z,
                finger_joints=[
                        [UP, 1, 4],
                        [DOWN, 1, 4],
                        [LEFT, 0, 4],
                        [RIGHT, 1, 4]
                    ]
            );
        }

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
                [UP, 0, 4],
                [DOWN, 0, 4],
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
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        bumpy_finger_joints=[
                [UP, 1, 4],
                [DOWN, 0, 4]
        ],
        cutouts = [[screw_offset_y + 28.701, 2+pcb+thickness, 9, 11]]
    );
    
color("Gold",0.75)
// right
translate([x,0,0])
    rotate([0,90,0]) 
    lasercutoutSquare(thickness=thickness, x=z, y=y,
        finger_joints=[
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        bumpy_finger_joints=[
                [UP, 1, 4],
                [DOWN, 0, 4],        
            ],
         circles_remove=[[4, screw_offset_y + 28.701 +2, y/2]]
    );