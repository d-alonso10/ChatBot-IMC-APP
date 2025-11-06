// lib/providers/paciente_provider.dart
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/paciente_model.dart';

class PacienteProvider extends ChangeNotifier {
  List<Paciente> _pacientes = [];
  final String? _authToken;

  List<Paciente> get pacientes => [..._pacientes];

  PacienteProvider(this._authToken, this._pacientes);

  Future<void> fetchPacientes() async {
    if (_authToken == null) return;
    try {
      final data = await ApiService.getPacientes(_authToken);
      _pacientes = data.map((item) => Paciente.fromJson(item)).toList();
      notifyListeners();
    } catch (e) {
      print("Error fetching pacientes: $e");
      // Manejar error...
    }
  }

  Future<void> addPaciente(String nombre, DateTime fechaNacimiento, String sexo) async {
    if (_authToken == null) return;
    try {
      final nuevoPacienteData = await ApiService.createPaciente(
        _authToken,
        nombre,
        fechaNacimiento.toIso8601String().split('T')[0], // Formato YYYY-MM-DD
        sexo,
      );
      final nuevoPaciente = Paciente.fromJson(nuevoPacienteData);
      _pacientes.add(nuevoPaciente);
      notifyListeners();
    } catch (e) {
      print("Error adding paciente: $e");
      rethrow;
    }
  }
}