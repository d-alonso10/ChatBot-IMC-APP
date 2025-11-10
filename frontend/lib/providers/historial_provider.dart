// lib/providers/historial_provider.dart
import 'dart:typed_data';
import 'package:flutter/foundation.dart'; // Para kIsWeb (web vs mobile)
import '../models/calculo_model.dart';
import '../services/api_service.dart';

// --- Dependencias para Descarga (Nuevas) ---
import 'package:url_launcher/url_launcher.dart';
import 'package:file_saver/file_saver.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:open_filex/open_filex.dart';

enum HistorialEstado { inicial, cargando, exito, error, sinDatos }

class HistorialProvider extends ChangeNotifier {
  final String _authToken;
  final int _pacienteId;
  final String _pacienteNombre;

  HistorialEstado _estado = HistorialEstado.inicial;
  List<Calculo> _calculos = [];
  String _error = '';

  // --- AHORA TENEMOS 3 GRÁFICOS ---
  Uint8List? _graficoIMCBytes;
  Uint8List? _graficoPesoBytes;
  Uint8List? _graficoTallaBytes;

  // --- Getters ---
  HistorialEstado get estado => _estado;
  List<Calculo> get calculos => _calculos;
  String get error => _error;
  Uint8List? get graficoIMCBytes => _graficoIMCBytes;
  Uint8List? get graficoPesoBytes => _graficoPesoBytes;
  Uint8List? get graficoTallaBytes => _graficoTallaBytes;

  HistorialProvider(this._authToken, this._pacienteId, this._pacienteNombre) {
    fetchHistorial();
  }

  Future<void> fetchHistorial() async {
    _estado = HistorialEstado.cargando;
    notifyListeners();
    
    try {
      // --- LÓGICA MODIFICADA: Cargar todo en paralelo ---
      
      // 1. Pedimos los cálculos primero.
      _calculos = (await ApiService.getHistorialCalculos(_authToken, _pacienteId))
          .map((data) => Calculo.fromJson(data))
          .toList();

      if (_calculos.isEmpty) {
        // 2. Si no hay cálculos, no hay nada que graficar.
        _estado = HistorialEstado.sinDatos;
      } else {
        // 3. Si SÍ hay cálculos, pedimos los 3 gráficos en paralelo.
        final results = await Future.wait([
          ApiService.getHistorialGraficoBytes(_authToken, _pacienteId),
          ApiService.getGraficoPesoBytes(_authToken, _pacienteId),
          ApiService.getGraficoTallaBytes(_authToken, _pacienteId),
        ]);
        
        _graficoIMCBytes = results[0] as Uint8List;
        _graficoPesoBytes = results[1] as Uint8List;
        _graficoTallaBytes = results[2] as Uint8List;
        
        _estado = HistorialEstado.exito;
      }
      // --- FIN LÓGICA MODIFICADA ---

    } catch (e) {
      _error = e.toString().replaceAll("Exception: ", "");
      if (_error.contains("404") || _error.contains("No hay historial")) {
        _estado = HistorialEstado.sinDatos;
      } else {
        _estado = HistorialEstado.error;
      }
    }
    notifyListeners();
  }

  // --- ¡NUEVA FUNCIÓN DE DESCARGA! ---
  Future<String> descargarPDF() async {
    try {
      final bytes = await ApiService.getPdfBytes(_authToken, _pacienteId);
      final pdfData = Uint8List.fromList(bytes);
      final filename = "Reporte_${_pacienteNombre.replaceAll(' ', '_')}.pdf";

      if (kIsWeb) {
        // --- LÓGICA PARA WEB ---
        // Usamos FileSaver para simular una descarga
        await FileSaver.instance.saveFile(
          name: filename,
          bytes: pdfData,
          ext: 'pdf',
          mimeType: MimeType.pdf,
        );
      } else {
        // --- LÓGICA PARA MÓVIL (Android/iOS) ---
        // 1. Pedir permiso
        var status = await Permission.storage.request();
        if (status.isGranted) {
          // 2. Obtener ruta de descargas
          final dir = await getApplicationDocumentsDirectory();
          final path = '${dir.path}/$filename';
          
          // 3. Guardar el archivo
          await FileSaver.instance.saveAs(
            name: filename,
            bytes: pdfData,
            ext: 'pdf',
            mimeType: MimeType.pdf
          );
          
          // 4. (Opcional) Abrir el archivo
          await OpenFilex.open(path);
          
        } else {
          return "Permiso de almacenamiento denegado.";
        }
      }
      return "¡PDF descargado con éxito!";
    } catch (e) {
      return "Error al descargar PDF: $e";
    }
  }
}