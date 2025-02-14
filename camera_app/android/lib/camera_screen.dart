import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _controller;
  late List<CameraDescription> _cameras;
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    initializeCamera();
  }

  Future<void> initializeCamera() async {
    _cameras = await availableCameras();
    _controller = CameraController(
      _cameras[0], // Use the first available camera
      ResolutionPreset.high,
    );

    await _controller.initialize();
    setState(() {
      _isInitialized = true;
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      appBar: AppBar(title: Text('Camera')),
      body: CameraPreview(_controller),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final image = await _controller.takePicture();
          print('Image saved at ${image.path}');
        },
        child: Icon(Icons.camera_alt),
      ),
    );
  }
}
