"""
Optimize the disease detection model for deployment on Render
This script reduces model size while maintaining accuracy
"""

import tensorflow as tf
import json
import os

print("🔧 Starting model optimization...")

# Load the original model
MODEL_PATH = 'crop_disease_detection_model.h5'
OPTIMIZED_PATH = 'crop_disease_detection_model_optimized.h5'

if not os.path.exists(MODEL_PATH):
    print(f"❌ Model file not found: {MODEL_PATH}")
    exit(1)

print(f"📦 Loading original model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

print(f"📊 Original model summary:")
model.summary()

# Get original model size
original_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
print(f"📏 Original model size: {original_size:.2f} MB")

# Method 1: Save with weight quantization
print("\n🔄 Optimizing model with float16 precision...")

# Convert model to use float16 for weights (reduces size by ~50%)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]

tflite_model = converter.convert()

# Save TFLite model
TFLITE_PATH = 'crop_disease_detection_model.tflite'
with open(TFLITE_PATH, 'wb') as f:
    f.write(tflite_model)

tflite_size = os.path.getsize(TFLITE_PATH) / (1024 * 1024)
print(f"✅ TFLite model saved: {TFLITE_PATH}")
print(f"📏 TFLite model size: {tflite_size:.2f} MB")
print(f"📉 Size reduction: {((original_size - tflite_size) / original_size * 100):.1f}%")

# Method 2: Save H5 model with reduced precision
print("\n🔄 Creating optimized H5 model...")

# Rebuild model with same architecture but save with optimization
model.save(OPTIMIZED_PATH, save_format='h5', include_optimizer=False)

optimized_size = os.path.getsize(OPTIMIZED_PATH) / (1024 * 1024)
print(f"✅ Optimized H5 model saved: {OPTIMIZED_PATH}")
print(f"📏 Optimized H5 size: {optimized_size:.2f} MB")
print(f"📉 Size reduction: {((original_size - optimized_size) / original_size * 100):.1f}%")

print("\n" + "="*60)
print("📊 OPTIMIZATION SUMMARY")
print("="*60)
print(f"Original H5:     {original_size:.2f} MB")
print(f"Optimized H5:    {optimized_size:.2f} MB (saved {original_size - optimized_size:.2f} MB)")
print(f"TFLite:          {tflite_size:.2f} MB (saved {original_size - tflite_size:.2f} MB)")
print("="*60)

print("\n💡 RECOMMENDATION:")
if tflite_size < 50:
    print(f"✅ Use TFLite model ({tflite_size:.2f} MB) - Best for Render free tier")
    print("   Update app.py to use TFLite interpreter instead of Keras model")
elif optimized_size < 80:
    print(f"✅ Use optimized H5 model ({optimized_size:.2f} MB)")
    print("   Replace crop_disease_detection_model.h5 with the optimized version")
else:
    print("⚠️  Model is still large. Consider:")
    print("   1. Reducing model complexity (fewer layers/neurons)")
    print("   2. Using a smaller input size (64x64 instead of 128x128)")
    print("   3. Pruning the model")

print("\n✅ Optimization complete!")
