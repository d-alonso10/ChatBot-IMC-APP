// lib/screens/historial_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/paciente_model.dart';
import '../providers/auth_provider.dart';
import '../providers/chat_provider.dart';
import '../providers/historial_provider.dart';
import 'chat_screen.dart';
import 'package:intl/intl.dart'; // Necesitaremos esto para formatear fechas

class HistorialScreen extends StatelessWidget {
  final Paciente paciente;
  const HistorialScreen({Key? key, required this.paciente}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authToken = Provider.of<AuthProvider>(context, listen: false).token!;

    // Usamos un provider que se crea a sí mismo para esta pantalla
    return ChangeNotifierProvider(
      create: (_) => HistorialProvider(authToken, paciente.id),
      child: Scaffold(
        backgroundColor: const Color(0xFFF8F5FB),
        appBar: AppBar(
          backgroundColor: const Color(0xFF7E57C2),
          elevation: 8,
          iconTheme: const IconThemeData(color: Colors.white),
          title: Text(
            'Historial de ${paciente.nombre}',
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
        ),
        body: Consumer<HistorialProvider>(
          builder: (ctx, historial, child) {
            switch (historial.estado) {
              case HistorialEstado.cargando:
                return const Center(child: CircularProgressIndicator());
              
              case HistorialEstado.error:
                return Center(
                  child: Text('Error al cargar el historial: ${historial.error}'),
                );
              
              case HistorialEstado.sinDatos:
                return _buildEmptyState(context, paciente, authToken);
              
              case HistorialEstado.exito:
                return _buildHistorialBody(context, historial, paciente, authToken);
              
              default:
                return const Center(child: Text('Cargando...'));
            }
          },
        ),
      ),
    );
  }

  // Widget para cuando SÍ hay historial
  Widget _buildHistorialBody(BuildContext context, HistorialProvider historial, Paciente paciente, String authToken) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // --- 1. El Gráfico ---
            Text(
              'Curva de Crecimiento',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            if (historial.graficoBytes != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(15),
                child: Image.memory(historial.graficoBytes!),
              )
            else
              const Center(child: Text('No se pudo cargar el gráfico.')),
            
            const SizedBox(height: 24),

            // --- 2. Botón de Nuevo Cálculo ---
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.add),
                label: const Text('INICIAR NUEVO CÁLCULO', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF7E57C2),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () => _iniciarNuevoCalculo(context, paciente, authToken),
              ),
            ),

            const SizedBox(height: 24),
            
            // --- 3. Lista de Cálculos Anteriores ---
            Text(
              'Registros Anteriores',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            ListView.builder(
              shrinkWrap: true, // Para que funcione dentro de SingleChildScrollView
              physics: const NeverScrollableScrollPhysics(), // Desactiva scroll de la lista
              itemCount: historial.calculos.length,
              itemBuilder: (ctx, i) {
                final calculo = historial.calculos[i];
                final fechaFormateada = DateFormat('dd/MM/yyyy').format(calculo.timestamp);
                return Card(
                  elevation: 2,
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFFEDE7F6),
                      child: Text(
                        calculo.imc?.toStringAsFixed(1) ?? '?',
                        style: const TextStyle(
                          color: Color(0xFF7E57C2),
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    title: Text(
                      calculo.clasificacion ?? 'Incompleto',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    subtitle: Text('Peso: ${calculo.peso} kg, Talla: ${calculo.talla} m'),
                    trailing: Text(fechaFormateada, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  // Widget para cuando NO hay historial
  Widget _buildEmptyState(BuildContext context, Paciente paciente, String authToken) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.history_rounded, size: 100, color: Colors.grey),
            const SizedBox(height: 20),
            Text(
              'Sin Historial',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Text(
              'Aún no hay cálculos para ${paciente.nombre}. ¡Vamos a crear el primero!',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, color: Colors.black54),
            ),
            const SizedBox(height: 30),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.add),
                label: const Text('INICIAR PRIMER CÁLCULO', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF7E57C2),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: () => _iniciarNuevoCalculo(context, paciente, authToken),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Función para navegar al chat
  void _iniciarNuevoCalculo(BuildContext context, Paciente paciente, String authToken) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (ctx) => ChangeNotifierProvider(
          create: (_) => ChatProvider(
            paciente: paciente,
            authToken: authToken,
          ),
          child: const ChatScreen(),
        ),
      ),
    );
  }
}