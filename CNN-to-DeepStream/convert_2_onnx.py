## pip install -U tensorflow tf2onnx

import numpy as np
import tensorflow as tf 
from tensorflow import keras
import tf2onnx

# It can be used to reconstruct the model identically.
model = keras.models.load_model('gender/content/gender_model.h5')

# model.add(keras.layers.Reshape((1, 224, 224,3)))

print(model.input_shape)
print(model.output_shape)
print(model.summary())


# arr = [1,3,224,224]
arr = [1,224,224,3]

model_proto, external_tensor_storage = tf2onnx.convert.from_keras(model,
                input_signature=None, opset=None, custom_ops=None,
                custom_op_handlers=None, custom_rewriter=None,
                inputs_as_nchw=arr, outputs_as_nchw=None, extra_opset=None,
                shape_override=None, target=None, large_model=False, output_path=None)


with open("./gender.onnx", "wb") as f:
    f.write(model_proto.SerializeToString())

print('\n\n[INFO] model to onnx was successful..')

#python3 -m tf2onnx.convert --saved-model tmp_model --output "model.onnx"