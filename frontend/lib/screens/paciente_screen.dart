// lib/screens/paciente_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/paciente_provider.dart';
import '../models/paciente_model.dart';
import '../providers/chat_provider.dart';
import 'chat_screen.dart';

// Imports de las pantallas que faltaban
import 'historial_screen.dart';
import 'package:intl/intl.dart';

class PacienteScreen extends StatefulWidget {
  const PacienteScreen({Key? key}) : super(key: key);

  @override
  _PacienteScreenState createState() => _PacienteScreenState();
}

class _PacienteScreenState extends State<PacienteScreen> {
  late Future _pacientesFuture;

  @override
  void initState() {
    super.initState();
    _pacientesFuture =
        Provider.of<PacienteProvider>(context, listen: false).fetchPacientes();
  }

  void _mostrarDialogAddPaciente(BuildContext context) {
    final nombreController = TextEditingController();
    final fechaNacController = TextEditingController();
    String? sexoValue; // 'niño' o 'niña'

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Añadir Nuevo Paciente'),
        content: StatefulBuilder(
          builder: (BuildContext context, StateSetter setState) {
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                    controller: nombreController,
                    decoration: const InputDecoration(labelText: 'Nombre')),
                TextField(
                  controller: fechaNacController,
                  decoration: const InputDecoration(
                      labelText: 'Fecha Nacimiento (YYYY-MM-DD)'),
                  readOnly: true, // Evitar que el teclado aparezca
                  onTap: () async {
                    FocusScope.of(context)
                        .requestFocus(FocusNode()); // Ocultar teclado
                    DateTime? picked = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now(),
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    
                    // --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
                    // Solo actualiza el texto si 'picked' no es null
                    if (picked != null) {
                      fechaNacController.text =
                          picked.toIso8601String().split('T')[0];
                    }
                    // --- FIN DE LA CORRECCIÓN ---
                  },
                ),
                DropdownButtonFormField<String>(
                  hint: const Text('Sexo'),
                  value: sexoValue,
                  onChanged: (value) {
                    setState(() {
                      sexoValue = value;
                    });
                  },
                  items: [
                    const DropdownMenuItem(value: 'niño', child: Text('Niño')),
                    const DropdownMenuItem(value: 'niña', child: Text('Niña')),
                  ],
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              if (nombreController.text.isNotEmpty &&
                  fechaNacController.text.isNotEmpty &&
                  sexoValue != null) {
                try {
                  await Provider.of<PacienteProvider>(context, listen: false)
                      .addPaciente(
                    nombreController.text,
                    DateTime.parse(fechaNacController.text),
                    sexoValue!,
                  );
                  Navigator.of(ctx).pop();
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error al crear paciente: $e')),
                  );
                }
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                      content: Text('Todos los campos son requeridos')),
                );
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis Pacientes'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              Provider.of<AuthProvider>(context, listen: false).logout();
            },
          ),
        ],
      ),
      body: FutureBuilder(
        future: _pacientesFuture,
        builder: (ctx, snapshot) =>
            snapshot.connectionState == ConnectionState.waiting
                ? const Center(child: CircularProgressIndicator())
                : Consumer<PacienteProvider>(
                    builder: (ctx, pacienteData, child) =>
                        pacienteData.pacientes.isEmpty
                            ? const Center(
                                child: Text("No tienes pacientes. ¡Añade uno!"))
                            : ListView.builder(
                                itemCount: pacienteData.pacientes.length,
                                itemBuilder: (ctx, i) {
                                  final paciente = pacienteData.pacientes[i];
                                  return _buildPacienteCard(context, paciente);
                                },
                              ),
                  ),
      ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.add),
        onPressed: () => _mostrarDialogAddPaciente(context),
      ),
    );
  }

  // Widget de la tarjeta de paciente (modificado para ir a HistorialScreen)
  Widget _buildPacienteCard(BuildContext context, Paciente paciente) {
    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (ctx) => HistorialScreen(paciente: paciente),
          ),
        );
      },
      child: Card(
        elevation: 4,
        shadowColor: Colors.deepPurple.withOpacity(0.1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: const Color(0xFFEDE7F6),
            child: Icon(
              paciente.sexo == 'niño' ? Icons.boy : Icons.girl,
              color: const Color(0xFF7E57C2),
            ),
          ),
          title: Text(paciente.nombre,
              style:
                  const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          subtitle: Text(
              'Nacimiento: ${DateFormat('dd/MM/yyyy').format(paciente.fechaNacimiento)}'),
          trailing:
              const Icon(Icons.analytics_outlined, color: Color(0xFF7E57C2)),
        ),
      ),
    );
  }
}