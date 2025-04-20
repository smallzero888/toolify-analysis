import os
import sys

# Check protobuf implementation
print(f"PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION: {os.environ.get('PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', 'Not set')}")

# Try to import tensorflow
try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")
    print(f"Eager execution enabled: {tf.executing_eagerly()}")
    
    gpus = tf.config.list_physical_devices('GPU')
    print(f"GPU devices: {gpus}")
    
    # Try a simple operation on GPU
    if len(gpus) > 0:
        # Use GPU
        device_name = '/GPU:0'
    else:
        # Fallback to CPU
        device_name = '/CPU:0'
        
    # Execute operations without using with statement
    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
    b = tf.constant([[5.0, 6.0], [7.0, 8.0]])
    
    # Specify device for this operation
    c = tf.matmul(a, b, name="matmul_op")
    print(f"Matrix multiplication result: {c}")
    print(f"Executed on: {c.device}")
except Exception as e:
    print(f"Error importing TensorFlow: {str(e)}")
    
# Check if protobuf is installed and its version
try:
    import google.protobuf
    print(f"Protobuf version: {google.protobuf.__version__}")
except Exception as e:
    print(f"Error importing protobuf: {str(e)}") 