
import math
import struct
import os

class GeometryEngine:
    """
    NEEMA Geometry Engine.
    Parses STL files and calculates physical properties (Volume, Bounding Box).
    """

    @staticmethod
    def analyze_stl(filepath: str):
        """
        Parses an ASCII STL file and returns {volume, bbox_x, bbox_y, bbox_z}.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CAD file not found: {filepath}")

        # Basic state
        triangles = []
        
        # Parse (Naive ASCII STL Parser)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        current_tri = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
                
            if parts[0] == 'vertex':
                # Vertex x y z
                v = (float(parts[1]), float(parts[2]), float(parts[3]))
                current_tri.append(v)
                
            if parts[0] == 'endloop':
                if len(current_tri) == 3:
                    triangles.append(current_tri)
                current_tri = []

        # Calculations
        volume = GeometryEngine.calculate_volume(triangles)
        bbox = GeometryEngine.calculate_bounds(triangles)
        
        return {
            "volume": volume,
            "bbox_width": bbox[1] - bbox[0],
            "bbox_depth": bbox[3] - bbox[2],
            "bbox_height": bbox[5] - bbox[4]
        }

    @staticmethod
    def calculate_volume(triangles):
        """
        Calculates volume of a closed mesh using the signed tetrahedron volume method.
        Vol = sum( dot(p1, cross(p2, p3)) ) / 6.0 for each triangle from origin
        """
        total_vol = 0.0
        for p1, p2, p3 in triangles:
            # Cross product of p2 and p3
            cp_x = p2[1]*p3[2] - p2[2]*p3[1]
            cp_y = p2[2]*p3[0] - p2[0]*p3[2]
            cp_z = p2[0]*p3[1] - p2[1]*p3[0]
            
            # Dot product with p1
            dot = p1[0]*cp_x + p1[1]*cp_y + p1[2]*cp_z
            total_vol += dot
            
        return abs(total_vol) / 6.0

    @staticmethod
    def calculate_bounds(triangles):
        """Returns [min_x, max_x, min_y, max_y, min_z, max_z]"""
        if not triangles:
            return [0,0,0,0,0,0]
            
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        for tri in triangles:
            for v in tri:
                if v[0] < min_x: min_x = v[0]
                if v[0] > max_x: max_x = v[0]
                if v[1] < min_y: min_y = v[1]
                if v[1] > max_y: max_y = v[1]
                if v[2] < min_z: min_z = v[2]
                if v[2] > max_z: max_z = v[2]
                
        return [min_x, max_x, min_y, max_y, min_z, max_z]

if __name__ == "__main__":
    # Test with a dummy file if running directly
    print("GeometryEngine loaded.")
