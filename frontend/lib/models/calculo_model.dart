// lib/models/calculo_model.dart

class Calculo {
  final String id;
  final double? peso;
  final double? talla;
  final double? imc;
  final String? clasificacion;
  final DateTime timestamp;
  final int pacienteId;

  Calculo({
    required this.id,
    this.peso,
    this.talla,
    this.imc,
    this.clasificacion,
    required this.timestamp,
    required this.pacienteId,
  });

  factory Calculo.fromJson(Map<String, dynamic> json) {
    return Calculo(
      id: json['id'],
      peso: json['peso']?.toDouble(),
      talla: json['talla']?.toDouble(),
      imc: json['imc']?.toDouble(),
      clasificacion: json['clasificacion'],
      timestamp: DateTime.parse(json['timestamp']),
      pacienteId: json['paciente_id'],
    );
  }
}