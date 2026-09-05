import 'dart:async';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

/// Reads raw multipart/x-mixed-replace MJPEG byte stream from ESP32-CAM
/// and yields individual JPEG frames as [Uint8List].
class MjpegStreamClient {
  final String streamUrl;
  StreamSubscription? _subscription;
  final StreamController<Uint8List> _frameController = StreamController<Uint8List>.broadcast();

  bool _isConnected = false;
  bool get isConnected => _isConnected;
  Stream<Uint8List> get frameStream => _frameController.stream;

  MjpegStreamClient({required this.streamUrl});

  void start() async {
    final client = http.Client();
    final request = http.Request('GET', Uri.parse(streamUrl));
    request.headers['User-Agent'] = 'Indriyo-ThrottleIQ-Flutter';

    try {
      final response = await client.send(request);
      if (response.statusCode == 200) {
        _isConnected = true;
        final List<int> buffer = [];

        _subscription = response.stream.listen((List<int> chunk) {
          buffer.addAll(chunk);

          // Find JPEG Start of Image (SOI) 0xFFD8 and End of Image (EOI) 0xFFD9
          while (true) {
            int soi = -1;
            for (int i = 0; i < buffer.length - 1; i++) {
              if (buffer[i] == 0xFF && buffer[i + 1] == 0xD8) {
                soi = i;
                break;
              }
            }

            if (soi == -1) {
              if (buffer.length > 500000) buffer.clear();
              break;
            }

            int eoi = -1;
            for (int i = soi + 2; i < buffer.length - 1; i++) {
              if (buffer[i] == 0xFF && buffer[i + 1] == 0xD9) {
                eoi = i + 2;
                break;
              }
            }

            if (eoi != -1) {
              final frameBytes = Uint8List.fromList(buffer.sublist(soi, eoi));
              _frameController.add(frameBytes);
              buffer.removeRange(0, eoi);
            } else {
              break;
            }
          }
        }, onError: (error) {
          _isConnected = false;
          _frameController.addError(error);
        }, onDone: () {
          _isConnected = false;
        }, cancelOnError: false);
      }
    } catch (e) {
      _isConnected = false;
      _frameController.addError(e);
    }
  }

  void stop() {
    _subscription?.cancel();
    _isConnected = false;
  }

  void dispose() {
    stop();
    _frameController.close();
  }
}
