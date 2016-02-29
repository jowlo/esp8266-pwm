include <lasercut.scad>; 
include <2d_m3-nutlock.scad>; 

thickness = 3;
pcb = 1.6;
x = 110;
y = 70 + 2*pcb;
z = 80;


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
    [screw_offset_x+usb_screw_offset_x + x*15.24, (10+pcb) + y*(30 +pcb) , 12.6, 11.3] ];


flash_cutout_w = 15;
flash_cutout_h = 4;
flash_cutout_y = 60+2*pcb;
flash_cutout_rect = [[(x - flash_cutout_w)/2, flash_cutout_y, flash_cutout_w, flash_cutout_h]];
flash_cutout_circ = [
    [flash_cutout_h/2, (x - flash_cutout_w)/2, flash_cutout_y + flash_cutout_h/2],
    [flash_cutout_h/2, (x - flash_cutout_w)/2 + flash_cutout_w, flash_cutout_y + flash_cutout_h/2]
];

module front() {
    union() {
        lasercutoutSquare(thickness=thickness, x=x, y=y,
            bumpy_finger_joints=[
                    [UP, 1, 8],
                    [DOWN, 1, 8],
                    [LEFT, 1, 4],
                    [RIGHT, 0, 4],
                ],
            cutouts = usb_cutouts
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
                    [UP, 0, 8],
                    [DOWN, 0, 8],
                    [LEFT, 1, 4],
                    [RIGHT, 0, 4],
                ],
            cutouts = flash_cutout_rect,
            circles_remove = flash_cutout_circ
            //,cutouts = [[(x-(2.54*8))/2, 10, 2.54*8, 2.54*2]]
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
                        [UP, 1, 8],
                        [DOWN, 1, 8],
                        [LEFT, 0, 4],
                        [RIGHT, 1, 4]
                    ],
                circles_remove = screw_holes
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
                [LEFT, 0, 4],
                [RIGHT, 1, 4]
            ],
        bumpy_finger_joints=[
                [UP, 1, 4],
                [DOWN, 0, 4]
        ],
        circles_remove = [
                [3, z-10, y-y/4], // antenna
                [4, z-10, y/4] // power
        ]
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
            ]        
    );

