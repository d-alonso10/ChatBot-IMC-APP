// lib/screens/paciente_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_staggered_animations/flutter_staggered_animations.dart';
import '../providers/auth_provider.dart';
import '../providers/paciente_provider.dart';
import '../models/paciente_model.dart';
import '../providers/chat_provider.dart';
import 'chat_screen.dart';
import 'historial_screen.dart';
import 'package:intl/intl.dart';

class PacienteScreen extends StatefulWidget {
  const PacienteScreen({Key? key}) : super(key: key);

  @override
  _PacienteScreenState createState() => _PacienteScreenState();
}

class _PacienteScreenState extends State<PacienteScreen> {
  late Future _pacientesFuture;

  // --- Definir los colores del tema ---
  static const Color primaryColor = Color(0xFF7E57C2);
  static const Color lightColor = Color(0xFFEDE7F6);
  static const Color backgroundColor = Color(0xFFF8F5FB);

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
        // --- ESTILO DEL DIÁLOGO MEJORADO ---
        backgroundColor: backgroundColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Añadir Nuevo Paciente',
            style: TextStyle(fontWeight: FontWeight.bold, color: primaryColor)),
        content: StatefulBuilder(
          builder: (BuildContext context, StateSetter setState) {
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                    controller: nombreController,
                    decoration:
                        const InputDecoration(labelText: 'Nombre')),
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
                      // --- TEMA DEL CALENDARIO ---
                      builder: (context, child) {
                        return Theme(
                          data: Theme.of(context).copyWith(
                            colorScheme: const ColorScheme.light(
                              primary: primaryColor, // color principal
                              onPrimary: Colors.white,
                              onSurface: Colors.black,
                            ),
                            textButtonTheme: TextButtonThemeData(
                              style: TextButton.styleFrom(
                                foregroundColor: primaryColor,
                              ),
                            ),
                          ),
                          child: child!,
                        );
                      },
                      // --- FIN TEMA ---
                    );
                    
                    if (picked != null) {
                      fechaNacController.text =
                          picked.toIso8601String().split('T')[0];
                    }
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
              child: const Text('Cancelar',
                  style: TextStyle(color: Colors.grey))),
          ElevatedButton(
            // --- ESTILO DE BOTÓN MEJORADO ---
            style: ElevatedButton.styleFrom(
              backgroundColor: primaryColor,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
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
      // --- COLOR DE FONDO AÑADIDO ---
      backgroundColor: backgroundColor,
      appBar: AppBar(
        // --- ESTILO DE APPBAR MEJORADO (COMO CHATSCREEN) ---
        backgroundColor: primaryColor,
        elevation: 8,
        shadowColor: Colors.deepPurple.withOpacity(0.3),
        iconTheme: const IconThemeData(color: Colors.white), // Para el botón de atrás
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child:
                  const Icon(Icons.family_restroom, color: Colors.white, size: 22),
            ),
            const SizedBox(width: 12),
            const Text(
              "Mis Pacientes",
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
                color: Colors.white,
              ),
            ),
          ],
        ),
        // --- FIN ESTILO APPBAR ---
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white),
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
                            ? const _EmptyState() // <-- WIDGET MEJORADO
                            : _buildAnimatedList(pacienteData.pacientes),
                  ),
      ),
      floatingActionButton: FloatingActionButton(
        // --- ESTILO FAB MEJORADO ---
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 6,
        child: const Icon(Icons.add),
        onPressed: () => _mostrarDialogAddPaciente(context),
      ),
    );
  }

  // --- WIDGET DE LISTA ANIMADA ---
  Widget _buildAnimatedList(List<Paciente> pacientes) {
    return AnimationLimiter(
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: pacientes.length,
        itemBuilder: (BuildContext context, int i) {
          final paciente = pacientes[i];
          return AnimationConfiguration.staggeredList(
            position: i,
            duration: const Duration(milliseconds: 375),
            child: SlideAnimation(
              verticalOffset: 50.0,
              child: FadeInAnimation(
                child: _buildPacienteCard(context, paciente),
              ),
            ),
          );
        },
      ),
    );
  }

  // --- WIDGET DE TARJETA DE PACIENTE (SIN CAMBIOS) ---
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
        margin: const EdgeInsets.symmetric(vertical: 8),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: lightColor,
            child: Icon(
              paciente.sexo == 'niño' ? Icons.boy : Icons.girl,
              color: primaryColor,
            ),
          ),
          title: Text(paciente.nombre,
              style:
                  const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          subtitle: Text(
              'Nacimiento: ${DateFormat('dd/MM/yyyy').format(paciente.fechaNacimiento)}'),
          trailing:
              const Icon(Icons.analytics_outlined, color: primaryColor),
        ),
      ),
    );
  }
}

// --- WIDGET HELPER PARA ESTADO VACÍO ---
class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.people_outline,
            size: 80,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            "No tienes pacientes",
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Toca el botón '+' para añadir tu primer paciente.",
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
            textAlign: TextAlign.center,
            softWrap: true,
            overflow: TextOverflow.clip,
          ),
        ],
      ),
    );
  }
}