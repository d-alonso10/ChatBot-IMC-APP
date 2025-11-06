// lib/models/paciente_model.dart
class Paciente {
  final int id;
  final String nombre;
  final DateTime fechaNacimiento;
  final String sexo;
  final int tutorId;

  Paciente({
    required this.id,
    required this.nombre,
    required this.fechaNacimiento,
    required this.sexo,
    required this.tutorId,
  });

  factory Paciente.fromJson(Map<String, dynamic> json) {
    return Paciente(
      id: json['id'],
      nombre: json['nombre'],
      fechaNacimiento: DateTime.parse(json['fecha_nacimiento']),
      sexo: json['sexo'],
      tutorId: json['tutor_id'],
    );
  }
}