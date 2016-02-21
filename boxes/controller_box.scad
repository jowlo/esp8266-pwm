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


color("Gold",0.75)
//front
    lasercutoutSquare(thickness=thickness, x=x, y=y,
        bumpy_finger_joints=[
                [UP, 1, 8],
                [DOWN, 1, 8],
                [LEFT, 1, 4],
                [RIGHT, 0, 4],
            ],
        cutouts = usb_cutouts
     );

// back
translate([0,0,-z - thickness])
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

// top
translate([0,y,0])
    rotate([-90,0,0]) 
    lasercutoutSquare(thickness=thickness, x=x, y=z,
        finger_joints=[
                [UP, 1, 8],
                [DOWN, 1, 8],
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        circles_remove = screw_holes
    );

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
        