// lib/screens/paciente_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/paciente_provider.dart';
import '../models/paciente_model.dart';
import '../providers/chat_provider.dart';
import 'chat_screen.dart';

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
    _pacientesFuture = Provider.of<PacienteProvider>(context, listen: false).fetchPacientes();
  }
  
  void _mostrarDialogAddPaciente(BuildContext context) {
    final nombreController = TextEditingController();
    final fechaNacController = TextEditingController();
    String? sexoValue; // 'niño' o 'niña'

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Añadir Nuevo Paciente'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nombreController, decoration: const InputDecoration(labelText: 'Nombre')),
            TextField(
              controller: fechaNacController,
              decoration: const InputDecoration(labelText: 'Fecha Nacimiento (YYYY-MM-DD)'),
              onTap: () async {
                FocusScope.of(context).requestFocus(FocusNode()); // Ocultar teclado
                DateTime? picked = await showDatePicker(
                  context: context,
                  initialDate: DateTime.now(),
                  firstDate: DateTime(2000),
                  lastDate: DateTime.now(),
                );
                if (picked != null) {
                  fechaNacController.text = picked.toIso8601String().split('T')[0];
                }
              },
            ),
            DropdownButtonFormField<String>(
              hint: const Text('Sexo'),
              value: sexoValue,
              onChanged: (value) {
                sexoValue = value;
              },
              items: [
                const DropdownMenuItem(value: 'niño', child: Text('Niño')),
                const DropdownMenuItem(value: 'niña', child: Text('Niña')),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () async {
              if (nombreController.text.isNotEmpty &&
                  fechaNacController.text.isNotEmpty &&
                  sexoValue != null) {
                try {
                  await Provider.of<PacienteProvider>(context, listen: false).addPaciente(
                    nombreController.text,
                    DateTime.parse(fechaNacController.text),
                    sexoValue!,
                  );
                  Navigator.of(ctx).pop();
                } catch (e) {
                  // Mostrar error
                }
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
        builder: (ctx, snapshot) => snapshot.connectionState == ConnectionState.waiting
            ? const Center(child: CircularProgressIndicator())
            : Consumer<PacienteProvider>(
                builder: (ctx, pacienteData, child) => ListView.builder(
                  itemCount: pacienteData.pacientes.length,
                  itemBuilder: (ctx, i) {
                    final paciente = pacienteData.pacientes[i];
                    return ListTile(
                      leading: Icon(paciente.sexo == 'niño' ? Icons.boy : Icons.girl),
                      title: Text(paciente.nombre),
                      subtitle: Text('Nacimiento: ${paciente.fechaNacimiento.toLocal().toString().split(' ')[0]}'),
                      onTap: () {
                        // Navegar al chat, pasando el paciente
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (ctx) => ChangeNotifierProvider(
                              create: (_) => ChatProvider(
                                paciente: paciente,
                                // Pasamos el token al ChatProvider
                                authToken: Provider.of<AuthProvider>(context, listen: false).token!,
                              ),
                              child: const ChatScreen(),
                            ),
                          ),
                        );
                      },
                    );
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
}