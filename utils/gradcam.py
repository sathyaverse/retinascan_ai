import numpy as np
import cv2
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def generate_gradcam(img_array, model_path, class_idx, original_image_path, output_path):
    """
    Generate a Grad-CAM heatmap overlay on the original retinal image.

    Args:
        img_array: preprocessed image array (1, 224, 224, 3)
        model_path: path to dr_model.h5
        class_idx: integer index of predicted class
        original_image_path: path to the original uploaded image
        output_path: where to save the heatmap overlay

    Returns:
        output_path if successful, None on failure
    """
    try:
        import tensorflow as tf

        model = tf.keras.models.load_model(model_path)

        # Find the last convolutional layer
        last_conv_layer = None
        for layer in reversed(model.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                last_conv_layer = layer.name
                break

        if last_conv_layer is None:
            print("[Grad-CAM] No Conv2D layer found.")
            return None

        # Build grad model
        grad_model = tf.keras.models.Model(
            inputs=model.input,
            outputs=[model.get_layer(last_conv_layer).output, model.output]
        )

        with tf.GradientTape() as tape:
            inputs = tf.cast(img_array, tf.float32)
            conv_outputs, predictions = grad_model(inputs)
            loss = predictions[:, class_idx]

        # Compute gradients
        grads = tape.gradient(loss, conv_outputs)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
        heatmap = heatmap.numpy()

        # Resize heatmap to original image size
        original = cv2.imread(original_image_path)
        h, w = original.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h))

        # Convert to color heatmap
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Overlay on original image
        overlay = cv2.addWeighted(original, 0.6, heatmap_colored, 0.4, 0)
        cv2.imwrite(output_path, overlay)

        return output_path

    except Exception as e:
        print(f"[Grad-CAM] Error: {e}")
        return None
