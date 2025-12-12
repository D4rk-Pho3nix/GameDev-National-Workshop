# made by Dark_Pho3nix
import copy

# =============================================================================
# GAME CONSTANTS
# =============================================================================
PIPEGAPSIZE = 100
PIPEWIDTH = 52
BIRDWIDTH = 34
BIRDHEIGHT = 24
# Safety margin: Act as if bird is slightly bigger to avoid grazing pipes
SAFETY_MARGIN = 2 
COLLISION_W = BIRDWIDTH + (SAFETY_MARGIN * 2)
COLLISION_H = BIRDHEIGHT + (SAFETY_MARGIN * 2)

SCREENWIDTH = 288
BASEY = 512 * 0.79
PIPE_VEL_X = -4
PLAYER_ACC_Y = 1
PLAYER_FLAP_ACC = -14
MAX_VEL_Y = 10
MIN_VEL_Y = -8
PLAYER_X = 57

class BeamSearchSolver:
    def __init__(self):
        self.last_path = []

    def check_collision(self, y, x_offset, lower_pipes):
        """
        Checks collision for a bird at (PLAYER_X, y) 
        given that pipes have moved by 'x_offset' from their original positions.
        """
        # 1. Ground/Sky
        if y + COLLISION_H >= BASEY - 1:
            return True
        if y < 0:
            return True # Treat ceiling as death to prevent flying over pipes cheat/bug

        # 2. Pipes
        # Bird static X = PLAYER_X.
        # Pipe effective X = pipe['x'] + x_offset.
        
        bird_left = PLAYER_X - SAFETY_MARGIN
        bird_right = PLAYER_X + BIRDWIDTH + SAFETY_MARGIN
        bird_top = y - SAFETY_MARGIN
        bird_bottom = y + BIRDHEIGHT + SAFETY_MARGIN

        for pipe in lower_pipes:
            px = pipe['x'] + x_offset
            
            # Optimization: Skip pipes that are gone or too far
            if px + PIPEWIDTH < bird_left: continue
            if px > bird_right: continue

            # Check overlap
            # Horizontal overlap is guaranteed by the 'continue' checks above
            
            # Gap Y range
            # pipe['y'] is the TOP of the LOWER pipe.
            # Gap is [pipe['y'] - PIPEGAPSIZE, pipe['y']]
            
            gap_top = pipe['y'] - PIPEGAPSIZE
            gap_bottom = pipe['y']
            
            # If we are NOT in the gap, we crashed.
            # In overlapping X, we are safe ONLY if:
            # bird_bottom < gap_bottom AND bird_top > gap_top
            
            # Alternatively, check collisions with solid parts:
            # Hit Lower Pipe? (Bird Bottom > Lower Pipe Top)
            if bird_bottom > gap_bottom:
                return True
            # Hit Upper Pipe? (Bird Top < Upper Pipe Bottom)
            if bird_top < gap_top:
                return True
                
        return False

    def get_gap_center(self, x_offset, lower_pipes):
        """Finds the Y center of the nearest relevant gap."""
        # Find first pipe that ends AFTER the bird
        bird_x = PLAYER_X
        
        target_y = BASEY / 2 # Default to middle of screen
        
        for pipe in lower_pipes:
            px = pipe['x'] + x_offset
            if px + PIPEWIDTH > bird_x:
                # Found the upcoming pipe
                return pipe['y'] - (PIPEGAPSIZE / 2) - (BIRDHEIGHT / 2)
        
        return target_y

    def solve(self, playery, playerVelY, lower_pipes):
        # Beam Search Parameters
        BEAM_WIDTH = 10   # Keep top 10 best paths
        LOOKAHEAD = 25    # Look 25 frames ahead (approx 1 sec)
        
        # Initial State: (Score, Y, Velocity, Path, FlapTakenAtFirstStep)
        # Score: Higher is better.
        current_states = [ (0, playery, playerVelY, [], None) ]
        
        # We need to preserve the decision of the FIRST step (Frame 0)
        # to return it at the end.
        
        for t in range(LOOKAHEAD):
            next_states = []
            x_offset = (t + 1) * PIPE_VEL_X
            target_y = self.get_gap_center(x_offset, lower_pipes)
            
            for score, y, vel, path, first_action in current_states:
                
                # Branch 1: Flap
                # Logic: vel += flap_acc (-9), then vel += acc (0 - skipped in game logic? wait)
                # Re-reading flappy.py logic:
                # If flap: vel += flap_acc (-14). flapped=True.
                # If not flapped: vel += acc.
                # So if flap, we DO NOT add gravity for that frame.
                
                vel_flap = vel + PLAYER_FLAP_ACC
                vel_flap = max(MIN_VEL_Y, min(MAX_VEL_Y, vel_flap))
                y_flap = y + vel_flap
                
                if not self.check_collision(y_flap, x_offset, lower_pipes):
                    # Calculate Heuristic Score
                    # 1. Distance to target (minimize)
                    dist = abs(y_flap - target_y)
                    # 2. Penalty for high velocity (stability)
                    vel_pen = abs(vel_flap) * 0.5
                    
                    new_score = score - dist - vel_pen
                    new_action = True if first_action is None else first_action
                    next_states.append( (new_score, y_flap, vel_flap, path + [(PLAYER_X, y_flap)], new_action) )

                # Branch 2: Do Nothing (Glide)
                # Logic: vel += acc (+1)
                vel_glide = vel + PLAYER_ACC_Y
                vel_glide = max(MIN_VEL_Y, min(MAX_VEL_Y, vel_glide))
                y_glide = y + vel_glide
                
                if not self.check_collision(y_glide, x_offset, lower_pipes):
                    dist = abs(y_glide - target_y)
                    vel_pen = abs(vel_glide) * 0.5
                    
                    new_score = score - dist - vel_pen
                    new_action = False if first_action is None else first_action
                    next_states.append( (new_score, y_glide, vel_glide, path + [(PLAYER_X, y_glide)], new_action) )

            # Pruning: Keep only top BEAM_WIDTH states
            if not next_states:
                # No survivors! We are doomed. 
                # Return anything to try and glitch through?
                # Usually best to Flap if dying low, Glide if dying high.
                return True, [] 
            
            # Sort by score (Descending - but our scores are negative, so effectively Ascending abs)
            next_states.sort(key=lambda x: x[0], reverse=True)
            current_states = next_states[:BEAM_WIDTH]

        # End of Search
        # Pick the absolute best survivor
        best_state = current_states[0]
        should_flap = best_state[4]
        self.last_path = best_state[3]
        
        return should_flap, self.last_path

# Global Singleton
solver = BeamSearchSolver()

def solve(playery, playerVelY, lowerPipes):
    return solver.solve(playery, playerVelY, lowerPipes)