// lib/screens/chat_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../widgets/message_bubble.dart';
import '../widgets/typing_indicator.dart';
import '../widgets/graph_image.dart';
import '../widgets/chat_input_field.dart';

class ChatScreen extends StatefulWidget {
  // Ya no recibe un Paciente, lo toma del Provider
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // El mensaje de bienvenida ahora se carga desde el constructor del ChatProvider
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    // Obtener el nombre del paciente desde el Provider
    final pacienteNombre = Provider.of<ChatProvider>(context, listen: false).paciente.nombre;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F5FB),
      appBar: AppBar(
        backgroundColor: const Color(0xFF7E57C2),
        elevation: 8,
        title: Text(
          "Cálculo para $pacienteNombre", // Título dinámico
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Consumer<ChatProvider>(
                  builder: (context, chatProvider, child) {
                    _scrollToBottom();
                    
                    return ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.only(top: 10, bottom: 10),
                      itemCount: chatProvider.messages.length,
                      itemBuilder: (ctx, i) {
                        final msg = chatProvider.messages[i];
                        
                        if (msg.isTyping) {
                          return const TypingIndicator();
                        }
                        
                        if (msg.imageUrl != null) {
                          return GraphImage(imageUrl: msg.imageUrl!);
                        }
                        
                        if (chatProvider.isBotTyping && 
                            i == chatProvider.messages.length - 1 && 
                            chatProvider.typingText.isNotEmpty) {
                          return MessageBubble(
                            text: chatProvider.typingText,
                            isUser: false,
                          );
                        }
                        
                        return MessageBubble(
                          text: msg.text ?? '',
                          isUser: msg.isUser,
                          isError: msg.isError,
                        );
                      },
                    );
                  },
                ),
              ),
            ),
            Consumer<ChatProvider>(
              builder: (context, chatProvider, child) {
                return ChatInputField(
                  // Modificamos onSendMessage para que no necesite pacienteId
                  onSendMessage: (text) => chatProvider.sendMessage(text),
                  isEnabled: !chatProvider.isBotTyping,
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}