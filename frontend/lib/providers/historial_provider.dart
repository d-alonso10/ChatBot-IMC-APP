// lib/providers/historial_provider.dart
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import '../models/calculo_model.dart';
import '../services/api_service.dart';

enum HistorialEstado { inicial, cargando, exito, error, sinDatos }

class HistorialProvider extends ChangeNotifier {
  final String _authToken;
  final int _pacienteId;

  HistorialEstado _estado = HistorialEstado.inicial;
  List<Calculo> _calculos = [];
  Uint8List? _graficoBytes;
  String _error = '';

  HistorialEstado get estado => _estado;
  List<Calculo> get calculos => _calculos;
  Uint8List? get graficoBytes => _graficoBytes;
  String get error => _error;

  HistorialProvider(this._authToken, this._pacienteId) {
    fetchHistorial();
  }

  Future<void> fetchHistorial() async {
    _estado = HistorialEstado.cargando;
    notifyListeners();
    
    try {
      // Pedir ambas cosas en paralelo
      final futureCalculos = ApiService.getHistorialCalculos(_authToken, _pacienteId);
      final futureGrafico = ApiService.getHistorialGraficoBytes(_authToken, _pacienteId);

      // Esperar a que ambas terminen
      final results = await Future.wait([futureCalculos, futureGrafico]);

      _calculos = (results[0]).map((data) => Calculo.fromJson(data)).toList();
      _graficoBytes = results[1] as Uint8List;

      if (_calculos.isEmpty) {
        _estado = HistorialEstado.sinDatos;
      } else {
        _estado = HistorialEstado.exito;
      }

    } catch (e) {
      _error = e.toString().replaceAll("Exception: ", "");
      // Si el error es 404 (sin historial), lo marcamos como "sinDatos"
      if (_error.contains("404") || _error.contains("No hay historial")) {
        _estado = HistorialEstado.sinDatos;
      } else {
        _estado = HistorialEstado.error;
      }
    }
    notifyListeners();
  }
}