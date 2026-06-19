import cv2
import pickle
import numpy as np
from pathlib import Path
import streamlit as st
import insightface

# =====================================
# 配置
# =====================================

FACE_DIR = Path("./face_data")
FACE_DIR.mkdir(exist_ok=True)

EMBEDDING_DIR = FACE_DIR / "embeddings"
EMBEDDING_DIR.mkdir(exist_ok=True)

SIMILARITY_THRESHOLD = 0.45

# =====================================
# InsightFace 初始化
# =====================================

face_model = insightface.app.FaceAnalysis(
    name="buffalo_s"
)

face_model.prepare(
    ctx_id=-1,
    det_size=(320, 320)
)

# =====================================
# 提取特征
# =====================================

def get_face_embedding(
    image: np.ndarray
):

    try:

        faces = face_model.get(image)

        if len(faces) == 0:
            return None

        face = max(
            faces,
            key=lambda x:
            (x.bbox[2] - x.bbox[0]) *
            (x.bbox[3] - x.bbox[1])
        )

        return face.normed_embedding

    except Exception as e:

        print("embedding error:", e)

        return None


# =====================================
# 保存人脸
# =====================================

def save_user_face(
    username: str,
    face_img: np.ndarray
):

    try:

        embedding = get_face_embedding(
            face_img
        )

        if embedding is None:
            return False

        save_path = (
            EMBEDDING_DIR /
            f"{username}.pkl"
        )

        with open(
            save_path,
            "wb"
        ) as f:

            pickle.dump(
                embedding,
                f
            )

        return True

    except Exception as e:

        print(
            "save_user_face:",
            e
        )

        return False


# =====================================
# 读取特征
# =====================================

def load_user_face(
    username: str
):

    try:

        path = (
            EMBEDDING_DIR /
            f"{username}.pkl"
        )

        if not path.exists():
            return None

        with open(
            path,
            "rb"
        ) as f:

            return pickle.load(f)

    except Exception as e:

        print(
            "load_user_face:",
            e
        )

        return None


# =====================================
# 人脸匹配
# =====================================

def match_face(
    username: str,
    face_img: np.ndarray
):

    try:

        saved_embedding = load_user_face(
            username
        )

        if saved_embedding is None:
            return False

        current_embedding = (
            get_face_embedding(
                face_img
            )
        )

        if current_embedding is None:
            return False

        similarity = np.dot(
            saved_embedding,
            current_embedding
        )

        print(
            f"similarity={similarity:.4f}"
        )

        return (
            similarity >
            SIMILARITY_THRESHOLD
        )

    except Exception as e:

        print(
            "match_face:",
            e
        )

        return False


# =====================================
# 摄像头采集（优化版）
# =====================================

def capture_face():

    cap = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():

        print("Camera open failed")

        return None

    saved_face = None

    SCALE = 0.5

    frame_count = 0

    cached_faces = []

    try:

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1

            if frame_count % 5 == 0:

                small_frame = cv2.resize(
                    frame,
                    None,
                    fx=SCALE,
                    fy=SCALE
                )

                try:

                    cached_faces = (
                        face_model.get(
                            small_frame
                        )
                    )

                except Exception:

                    cached_faces = []

            current_face = None

            for face in cached_faces:

                bbox = face.bbox.astype(
                    np.int32
                )

                x1, y1, x2, y2 = bbox

                x1 = int(x1 / SCALE)
                y1 = int(y1 / SCALE)
                x2 = int(x2 / SCALE)
                y2 = int(y2 / SCALE)

                h, w = frame.shape[:2]

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                current_face = frame[
                    y1:y2,
                    x1:x2
                ].copy()

            cv2.imshow(
                "Face Capture - SPACE Save - Q Quit",
                frame
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key == ord(" "):

                if current_face is not None:

                    saved_face = current_face

                    break

            if key == ord("q"):

                saved_face = None

                break

    finally:

        try:

            cap.release()

        except Exception:
            pass

        try:

            cv2.destroyAllWindows()

            cv2.waitKey(1)
            cv2.waitKey(1)
            cv2.waitKey(1)

        except Exception:
            pass

    return saved_face


# =====================================
# Streamlit 注册界面
# =====================================

def render_face_register(
    username: str
):

    st.subheader(
        "🪪 Face Register"
    )

    if st.button(
        "Start Capture"
    ):

        with st.spinner(
            "Capturing Face..."
        ):

            face = capture_face()

        if face is None:

            st.error(
                "No face detected"
            )

            return

        if save_user_face(
            username,
            face
        ):

            st.success(
                "Face Registered Successfully"
            )

        else:

            st.error(
                "Register Failed"
            )
#下面是保底
# import cv2
# import numpy as np
# from pathlib import Path
# import streamlit as st

# FACE_DIR = Path("./face_data")
# FACE_DIR.mkdir(exist_ok=True)

# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades +
#     "haarcascade_frontalface_alt2.xml"
# )


# def _get_face_recognizer():
#     return cv2.face.LBPHFaceRecognizer_create()


# def save_user_face(username: str, face_img: np.ndarray):
#     try:
#         gray = cv2.cvtColor(
#             face_img,
#             cv2.COLOR_BGR2GRAY
#         )

#         gray = cv2.resize(
#             gray,
#             (200, 200)
#         )

#         recognizer = _get_face_recognizer()

#         recognizer.train(
#             [gray],
#             np.array([1])
#         )

#         recognizer.save(
#             str(FACE_DIR / f"{username}.yml")
#         )

#         return True

#     except Exception as e:
#         print("save_user_face:", e)
#         return False


# def match_face(username: str, face_img: np.ndarray):
#     model_path = FACE_DIR / f"{username}.yml"

#     if not model_path.exists():
#         return False

#     try:
#         gray = cv2.cvtColor(
#             face_img,
#             cv2.COLOR_BGR2GRAY
#         )

#         gray = cv2.resize(
#             gray,
#             (200, 200)
#         )

#         recognizer = _get_face_recognizer()

#         recognizer.read(
#             str(model_path)
#         )

#         label, confidence = recognizer.predict(gray)

#         print(
#             f"label={label}, confidence={confidence}"
#         )

#         return confidence < 50

#     except Exception as e:
#         print("match_face:", e)
#         return False


# def capture_face():
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         print("Camera open failed")
#         return None

#     saved_face = None

#     while True:
#         ret, frame = cap.read()

#         if not ret:
#             break

#         gray = cv2.cvtColor(
#             frame,
#             cv2.COLOR_BGR2GRAY
#         )

#         faces = face_cascade.detectMultiScale(
#             gray,
#             scaleFactor=1.1,
#             minNeighbors=5,
#             minSize=(100, 100)
#         )

#         # 每帧重新置空，防止沿用上一帧的人脸
#         current_face = None

#         if len(faces) > 0:

#             # 选择最大的人脸
#             x, y, w, h = max(
#                 faces,
#                 key=lambda f: f[2] * f[3]
#             )

#             cv2.rectangle(
#                 frame,
#                 (x, y),
#                 (x + w, y + h),
#                 (0, 255, 0),
#                 2
#             )

#             current_face = frame[
#                 y:y + h,
#                 x:x + w
#             ].copy()

#             cv2.putText(
#                 frame,
#                 "Face Detected",
#                 (10, 35),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 1,
#                 (0, 255, 0),
#                 2
#             )

#         else:
#             cv2.putText(
#                 frame,
#                 "No Face",
#                 (10, 35),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 1,
#                 (0, 0, 255),
#                 2
#             )

#         cv2.imshow(
#             "Face Capture - SPACE Save - Q Quit",
#             frame
#         )

#         key = cv2.waitKey(1) & 0xFF

#         # 只有当前帧有人脸才保存
#         if key == ord(" "):
#             if current_face is not None:
#                 saved_face = current_face
#                 print("Face saved")
#                 break
#             else:
#                 print("No face in current frame")

#         if key == ord("q"):
#             saved_face = None
#             break

#     cap.release()
#     cv2.destroyAllWindows()

#     return saved_face


# def render_face_register(username: str):
#     st.subheader("🪪 Face Register")

#     if st.button("Start Capture"):
#         with st.spinner("Capturing Face..."):
#             face = capture_face()

#         if face is None:
#             st.error("No face captured")
#             return

#         if save_user_face(
#             username,
#             face
#         ):
#             st.success(
#                 "Face Registered Successfully"
#             )
#         else:
#             st.error(
#                 "Register Failed"
#             )