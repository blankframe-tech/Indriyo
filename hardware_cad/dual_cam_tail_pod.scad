// ==============================================================================
// Indriyo (ইন্দ্রিয়) - Dual ESP32-CAM Tail Stealth Pod
// Parametric 3D Printable Enclosure for Motorcycle Rearview ADAS
// ==============================================================================

$fn = 60;

// Dimensions (in millimeters)
wall_thickness = 2.4;
pod_width = 86;
pod_depth = 42;
pod_height = 36;
splay_angle = 15; // 15 degrees outward splay for each camera to cover blind spots
lens_diameter = 10.5;
lens_hood_depth = 5.0;

module camera_bracket() {
    difference() {
        // Module outer shell
        cube([28, 40, 26], center=true);
        // ESP32-CAM board cavity (AI-Thinker: 27 x 40.5 mm)
        cube([25, 41, 23], center=true);
        // Lens hole
        translate([0, -20, 0])
            rotate([90, 0, 0])
                cylinder(h=10, d=lens_diameter, center=true);
    }
    // Rain visor / sun hood
    translate([0, -21, 5])
        cube([18, lens_hood_depth, 3], center=true);
}

module indriyo_dual_pod() {
    difference() {
        // Main aerodynamic housing
        hull() {
            translate([-25, 0, 0]) rotate([0, 0, -splay_angle]) cube([32, pod_depth, pod_height], center=true);
            translate([25, 0, 0]) rotate([0, 0, splay_angle]) cube([32, pod_depth, pod_height], center=true);
        }

        // Left camera cavity
        translate([-25, 0, 0])
            rotate([0, 0, -splay_angle])
                cube([26, 42, 24], center=true);

        // Right camera cavity
        translate([25, 0, 0])
            rotate([0, 0, splay_angle])
                cube([26, 42, 24], center=true);

        // Left lens aperture
        translate([-25, 0, 0])
            rotate([0, 0, -splay_angle])
                translate([0, -25, 0])
                    rotate([90, 0, 0])
                        cylinder(h=20, d=lens_diameter, center=true);

        // Right lens aperture
        translate([25, 0, 0])
            rotate([0, 0, splay_angle])
                translate([0, -25, 0])
                    rotate([90, 0, 0])
                        cylinder(h=20, d=lens_diameter, center=true);

        // Rear wire exit canal
        translate([0, 20, 0])
            cube([16, 12, 10], center=true);

        // License plate bracket mounting slots (M4 / M5 screws)
        translate([-22, 12, pod_height/2 - 2])
            cylinder(h=10, d=4.5, center=true);
        translate([22, 12, pod_height/2 - 2])
            cylinder(h=10, d=4.5, center=true);
    }
}

indriyo_dual_pod();
