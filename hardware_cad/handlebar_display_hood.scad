// Indriyo (ইন্দ্রিয়) - Parametric Motorcycle Handlebar Display & Sun Hood
// Designed for OpenSCAD / FDM 3D Printing (PETG/ABS Recommended)

$fn = 60; // Smooth curves

// --- PARAMETERS ---
bar_diameter = 22.2;       // Standard 7/8" (22.2mm) handlebar (or 28.6mm for fatbars)
clamp_width = 24.0;        // Width of bar clamp
clamp_thickness = 4.5;     // Thickness of clamp band
display_width = 140.0;     // Accommodates up to 6.1" smartphone or 5" LCD display
display_height = 78.0;     // Display internal height
display_depth = 14.0;      // Device slot thickness
visor_depth = 28.0;        // Anti-glare sun hood extension length
visor_flare = 12.0;        // Outward visor angle flare
wall_thickness = 3.0;      // Enclosure wall thickness
cable_slot_w = 16.0;       // USB-C pass-through slot width
cable_slot_h = 8.0;        // USB-C pass-through slot height

module handlebar_clamp() {
    difference() {
        cylinder(r = (bar_diameter/2) + clamp_thickness, h = clamp_width, center = true);
        cylinder(r = bar_diameter/2, h = clamp_width + 1, center = true);
        // Clamp slit
        translate([0, (bar_diameter/2) + clamp_thickness/2, 0])
            cube([clamp_thickness * 2, 4, clamp_width + 2], center = true);
    }
    // Bolt tabs
    translate([(bar_diameter/2) + 6, (bar_diameter/2) + 2, 0])
        difference() {
            cube([12, 10, clamp_width], center = true);
            // M4 bolt hole
            rotate([90, 0, 0]) cylinder(r = 2.2, h = 14, center = true);
        }
}

module display_cradle() {
    difference() {
        // Outer housing shell
        cube([
            display_width + (wall_thickness * 2),
            display_height + (wall_thickness * 2),
            display_depth + wall_thickness
        ], center = true);

        // Internal device pocket
        translate([0, 0, wall_thickness / 2])
            cube([display_width, display_height, display_depth + 1], center = true);

        // USB-C Bottom charging / telemetry cable port
        translate([0, -(display_height/2 + wall_thickness/2), 0])
            cube([cable_slot_w, wall_thickness * 2, cable_slot_h], center = true);
            
        // Finger push-out slot for easy phone removal
        cylinder(r = 15, h = display_depth * 2, center = true);
    }
}

module sun_visor() {
    // 4-sided tapered glare-shield hood
    difference() {
        hull() {
            // Base matching cradle rim
            translate([0, 0, display_depth/2])
                cube([display_width + (wall_thickness * 2), display_height + (wall_thickness * 2), 1], center = true);
            // Flared front rim
            translate([0, visor_flare / 2, display_depth/2 + visor_depth])
                cube([display_width + (wall_thickness * 2) + (visor_flare * 2), display_height + (wall_thickness * 2) + visor_flare, 1], center = true);
        }
        hull() {
            // Cutout interior
            translate([0, 0, display_depth/2 - 1])
                cube([display_width, display_height, 1], center = true);
            translate([0, visor_flare / 2, display_depth/2 + visor_depth + 1])
                cube([display_width + (visor_flare * 2), display_height + visor_flare, 1], center = true);
        }
    }
}

// Complete Assembled Model
module full_assembly() {
    // Main Display Cradle & Sun Visor
    display_cradle();
    sun_visor();

    // Dual Bar Clamps (Left and Right for rigidity)
    translate([-45, -display_height/2 - 18, -10])
        rotate([0, 90, 0])
            handlebar_clamp();

    translate([45, -display_height/2 - 18, -10])
        rotate([0, 90, 0])
            handlebar_clamp();
}

full_assembly();
