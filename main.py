import cv2
import mediapipe as mp
import numpy as np
import time
import math
import random

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# ---------- utils ----------
def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def normalize_landmarks(landmarks, w, h):
    pts = []
    for lm in landmarks:
        pts.append((int(lm.x * w), int(lm.y * h)))
    return pts

def finger_is_up(pts, finger_tip_idx, finger_mcp_idx):
    return pts[finger_tip_idx][1] < pts[finger_mcp_idx][1]

def hand_depth(pts):
    # Use thumb-tip to index-tip distance as a simple depth proxy
    return dist(pts[4], pts[8])

# ---------- gesture rules ----------
def classify_gesture(pts):
    tips = [4, 8, 12, 16, 20]
    mcp = [2, 5, 9, 13, 17]

    pinch_dist = dist(pts[4], pts[8])
    if pinch_dist < 40:
        return "pinch"

    up_count = 0
    for tip_idx, mcp_idx in zip(tips[1:], mcp[1:]):
        if finger_is_up(pts, tip_idx, mcp_idx):
            up_count += 1

    if up_count >= 4:
        return "open_palm"
    if up_count == 0:
        return "fist"
    if up_count == 1 and finger_is_up(pts, 8, 5):
        return "index_only"
    return "unknown"

# ---------- Dr. Strange style alchemy circle ----------
#----------- Can also be Iron man Stuff ---------------- 
class AlchemyCircle:
    def __init__(self, center, hand_id):
        self.center = center
        self.hand_id = hand_id
        self.radius = 10
        self.target_radius = 120
        self.alpha = 0.0
        self.angle = 0.0
        self.active = False
        self.spawn_time = 0.0
        self.runes = []
        self.last_update = time.time()
        
        # RANDOMIZED PROPERTIES
        self.style = 'strange'
        self.polygon_sides = random.randint(5, 8)
        self.radial_lines = random.randint(8, 16)
        self.rotation_speed = random.uniform(40, 80)
        self.color_hue = random.randint(0, 2)
        self.num_rings = random.randint(3, 5)
        self.mandala_layers = random.randint(2, 4)
        self.counter_rotate = random.choice([True, False])

    def get_color_scheme(self):
        if self.color_hue == 0:  # purple/magenta
            return (180, 120, 255), (255, 255, 255), (220, 180, 255)
        elif self.color_hue == 1:  # cyan/blue
            return (255, 200, 100), (255, 255, 255), (255, 220, 150)
        else:  # orange/gold
            return (0, 165, 255), (255, 255, 255), (100, 200, 255)

    def spawn(self):
        self.active = True
        self.spawn_time = time.time()
        self.radius = 10
        self.alpha = 0.0
        self.runes = []
        self.target_radius = random.randint(70, 100)
        # Randomize properties each spawn
        self.style = 'strange'
        self.polygon_sides = random.randint(5, 8)
        self.radial_lines = random.randint(8, 16)
        self.rotation_speed = random.uniform(40, 80)
        self.color_hue = random.randint(0, 2)
        self.num_rings = random.randint(3, 5)
        self.mandala_layers = random.randint(2, 4)
        self.counter_rotate = random.choice([True, False])
        # Auto-spawn runes
        num_auto_runes = random.randint(2, 6)
        for _ in range(num_auto_runes):
            self.add_rune(random.uniform(0, 360))

    def spawn_auto(self):
        self.spawn()
        num_auto_runes = random.randint(3, 8)
        for _ in range(num_auto_runes):
            self.add_rune(random.uniform(0, 360))

    def dismiss(self):
        self.active = False

    def add_rune(self, angle):
        self.runes.append([angle, 0.0])

    def update_radius_based_on_depth(self, depth):
        """Map hand depth to circle size"""
        min_radius = 50
        max_radius = 200
        # depth roughly 20-150 pixels; map to radius
        mapped_radius = int(np.clip((depth - 20) / (150 - 20) * (max_radius - min_radius) + min_radius, min_radius, max_radius))
        self.target_radius = mapped_radius

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        if not self.active:
            return
        self.radius += (self.target_radius - self.radius) * 0.18
        self.alpha = min(1.0, self.alpha + dt * 2.0)
        self.angle += dt * self.rotation_speed
        for r in self.runes:
            if r[1] < 1.0:
                r[1] += dt * 1.2

    def draw_classic_style(self, img, cx, cy, r, color1, color2, color3):
        overlay = img.copy()
        for i in range(self.num_rings):
            rr = int(r * (1.0 + i * 0.12))
            thickness = 2
            alpha_ring = max(0.05, self.alpha * (0.6 - i*0.12))
            cv2.circle(overlay, (cx,cy), rr, color1, thickness=thickness)
            img = cv2.addWeighted(overlay, alpha_ring, img, 1 - alpha_ring, 0)

        pts = []
        for k in range(self.polygon_sides):
            theta = math.radians(self.angle + k * 360 / self.polygon_sides)
            x = int(cx + r*0.55 * math.cos(theta))
            y = int(cy + r*0.55 * math.sin(theta))
            pts.append((x,y))
        cv2.polylines(img, [np.array(pts, np.int32)], isClosed=True, color=color2, thickness=2)

        for k in range(self.radial_lines):
            theta = math.radians(self.angle + k * 360 / self.radial_lines)
            x1 = int(cx + r*0.7 * math.cos(theta))
            y1 = int(cy + r*0.7 * math.sin(theta))
            x2 = int(cx + r * math.cos(theta))
            y2 = int(cy + r * math.sin(theta))
            cv2.line(img, (x1,y1), (x2,y2), color1, 1)

        return img

    def draw_strange_style(self, img, cx, cy, r, color1, color2, color3):
        overlay = img.copy()
        for layer in range(self.mandala_layers):
            layer_radius = int(r * (0.3 + layer * 0.3))
            layer_angle = self.angle if not self.counter_rotate or layer % 2 == 0 else -self.angle
            alpha_val = self.alpha * 0.4
            cv2.circle(overlay, (cx, cy), layer_radius, color1, 2)
            img = cv2.addWeighted(overlay, alpha_val, img, 1 - alpha_val, 0)
            sides = 6 if layer % 2 == 0 else 8
            pts = []
            for k in range(sides):
                theta = math.radians(layer_angle + k * 360 / sides)
                x = int(cx + layer_radius * math.cos(theta))
                y = int(cy + layer_radius * math.sin(theta))
                pts.append((x,y))
            cv2.polylines(img, [np.array(pts, np.int32)], isClosed=True, color=color2, thickness=2)
            for k in range(sides):
                theta = math.radians(layer_angle + k * 360 / sides)
                x = int(cx + layer_radius * math.cos(theta))
                y = int(cy + layer_radius * math.sin(theta))
                cv2.line(img, (cx, cy), (x, y), color3, 1)
            for k in range(sides):
                theta = math.radians(layer_angle + k * 360 / sides)
                x = int(cx + layer_radius * math.cos(theta))
                y = int(cy + layer_radius * math.sin(theta))
                cv2.circle(img, (x, y), 3, color1, -1)

        num_arcs = 12
        for k in range(num_arcs):
            start_angle = int(self.angle + k * 360 / num_arcs)
            end_angle = int(start_angle + 25)
            cv2.ellipse(img, (cx, cy), (r, r), 0, start_angle, end_angle, color1, 2)

        for k in range(8):
            theta = math.radians(self.angle * 1.5 + k * 360 / 8)
            x = int(cx + r * 0.85 * math.cos(theta))
            y = int(cy + r * 0.85 * math.sin(theta))
            size = 8
            thickness = 2
            cv2.line(img, (x-size, y), (x+size, y), color2, thickness)
            cv2.line(img, (x, y-size), (x, y+size), color2, thickness)

        return img

    def draw(self, img):
        if not self.active:
            return img
        cx, cy = self.center
        r = int(self.radius)
        color1, color2, color3 = self.get_color_scheme()
        if self.style == 'strange':
            img = self.draw_strange_style(img, cx, cy, r, color1, color2, color3)
        else:
            img = self.draw_classic_style(img, cx, cy, r, color1, color2, color3)
        for angle, prog in self.runes:
            start = int(angle - 20)
            end = int(angle - 20 + prog * 40)
            cv2.ellipse(img, (cx,cy), (int(r*0.9), int(r*0.9)), 0, start, end, color3, 2)
        return img

# ---------- main ----------
def main():
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.5)

    circles = {}
    last_gestures = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)
        current_hands = set()

        if result.multi_hand_landmarks and result.multi_handedness:
            for idx, (hand_landmarks, handedness) in enumerate(zip(result.multi_hand_landmarks, result.multi_handedness)):
                hand_label = handedness.classification[0].label
                hand_id = hand_label
                current_hands.add(hand_id)
                pts = normalize_landmarks(hand_landmarks.landmark, w, h)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                gesture = classify_gesture(pts)
                wrist = pts[0]
                center = (wrist[0], wrist[1] - 100)

                if hand_id not in circles:
                    circles[hand_id] = AlchemyCircle(center, hand_id)
                    last_gestures[hand_id] = "none"

                # Update center smoothly
                circles[hand_id].center = (
                    int(circles[hand_id].center[0] * 0.8 + center[0] * 0.2),
                    int(circles[hand_id].center[1] * 0.8 + center[1] * 0.2)
                )

                # Update radius based on depth
                depth = hand_depth(pts)
                circles[hand_id].update_radius_based_on_depth(depth)

                # Gesture transitions
                last_gesture = last_gestures.get(hand_id, "none")
                if gesture == "pinch" and last_gesture != "pinch":
                    circles[hand_id].spawn()
                if gesture == "fist" and last_gesture != "fist":
                    circles[hand_id].dismiss()
                if gesture == "index_only" and last_gesture != "index_only":
                    idx_tip = pts[8]
                    dx = idx_tip[0] - circles[hand_id].center[0]
                    dy = idx_tip[1] - circles[hand_id].center[1]
                    angle = math.degrees(math.atan2(dy, dx))
                    circles[hand_id].add_rune(angle)
                # Auto-spawn if hand is open_palm
                if gesture == "open_palm" and not circles[hand_id].active:
                    circles[hand_id].spawn_auto()

                last_gestures[hand_id] = gesture

        # Dismiss circles for hands no longer visible
        hands_to_remove = []
        for hand_id in circles.keys():
            if hand_id not in current_hands:
                circles[hand_id].dismiss()
                hands_to_remove.append(hand_id)
        for hand_id in hands_to_remove:
            if hand_id in circles and not circles[hand_id].active:
                del circles[hand_id]
                if hand_id in last_gestures:
                    del last_gestures[hand_id]

        # Update and draw all circles
        for circle in circles.values():
            circle.update()
            frame = circle.draw(frame)

        cv2.putText(frame, f'Hands: {len(current_hands)}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, 'Pinch: Spawn | Fist: Dismiss', (10, h-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow('Alchemy Gestures - Dr. Strange Edition', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
