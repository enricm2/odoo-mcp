# CONTRATO DE LICENCIA DE USO DE SOFTWARE COMO SERVICIO (SaaS)
## IA Agents Treasury Control — Módulo para Odoo 18

**Versión 1.0 — Mayo 2026**

**Licenciante:** Uniasser Sistemas SL, con CIF B-XXXXXXXX, domicilio en [Dirección], inscrita en el Registro Mercantil de [Provincia].
**Contacto:** soporte@uniasser.com | legal@uniasser.com

---

## AVISO IMPORTANTE

**ANTES DE INSTALAR, ACTIVAR O UTILIZAR ESTE SOFTWARE, LEA ATENTAMENTE ESTE CONTRATO.**
La instalación, activación, descarga o cualquier uso del software implica la aceptación expresa,
plena e incondicional de todos los términos y condiciones que se recogen a continuación.
Si no acepta estos términos, no instale ni utilice el software y contacte con el Licenciante
para obtener un reembolso si procede.

---

## 1. DEFINICIONES

- **"Software"**: el módulo IA Agents Treasury Control para Odoo 18, incluyendo todos sus ficheros
  fuente, bytecode compilado, ficheros de configuración, vistas XML, scripts y documentación.
- **"Licenciante"**: Uniasser Sistemas SL, titular de todos los derechos de propiedad intelectual
  sobre el Software.
- **"Licenciatario"**: la persona física o jurídica que contrata el acceso al Software.
- **"Instancia"**: una única instalación de Odoo identificada por su `database.uuid`.
- **"Clave de Licencia"**: el identificador único emitido por el Licenciante que activa el Software
  para una Instancia determinada.
- **"Suscripción"**: el contrato de acceso periódico (mensual o anual) al Software y sus
  actualizaciones, sujeto al pago de la cuota establecida en el momento de la contratación.
- **"Servidor de Licencias"**: la infraestructura del Licenciante que valida las Claves de Licencia
  y emite los tokens de autorización.

---

## 2. CONCESIÓN DE LICENCIA

2.1. El Licenciante concede al Licenciatario, durante el período de vigencia de la Suscripción
activa y pagada, una licencia **no exclusiva, no transferible, no sublicenciable y revocable**
para:

- Instalar y ejecutar el Software en **una única Instancia** de Odoo 18.
- Utilizar las funcionalidades del Software conforme a la documentación oficial.
- Realizar copias de seguridad internas del Software únicamente con fines de recuperación ante
  desastres, sin que dichas copias otorguen derechos adicionales.

2.2. La licencia se activa mediante la Clave de Licencia y queda vinculada al `database.uuid`
de la primera Instancia en la que se active. No se puede transferir a otra Instancia sin
autorización escrita del Licenciante.

2.3. Cualquier uso del Software fuera del alcance definido en la cláusula 2.1 requerirá
una licencia adicional.

---

## 3. RESTRICCIONES DE USO

**Queda expresamente PROHIBIDO, sin perjuicio de las acciones legales y penales correspondientes:**

3.1. **Ingeniería inversa y descompilación.** Descompilar, desensamblar, descifrar, realizar
ingeniería inversa o intentar obtener el código fuente del Software o de cualquiera de sus
componentes protegidos, incluyendo los ficheros cifrados con PyArmor o cualquier otra
tecnología de protección.

3.2. **Manipulación del sistema de licencias.** Modificar, parchear, eliminar, eludir, deshabilitar
o de cualquier otro modo alterar los mecanismos de verificación de licencia, incluyendo pero
no limitado a: editar `license_manager.py`, modificar las llamadas al Servidor de Licencias,
sustituir o falsificar tokens JWT, o alterar cualquier parámetro de sistema relacionado
con la licencia (`ia_agents_treasury_control.license_*`).

3.3. **Distribución no autorizada.** Copiar, distribuir, vender, alquilar, prestar, sublicenciar,
publicar o transferir el Software o cualquier parte del mismo a terceros sin autorización
escrita previa del Licenciante.

3.4. **Uso en múltiples instancias.** Activar una única Clave de Licencia en más de una Instancia
simultáneamente, salvo contrato específico de licencia multi-instancia.

3.5. **Eliminación de avisos de propiedad.** Suprimir, modificar u ocultar cualquier aviso de
copyright, marca registrada, nombre del Licenciante o cualquier otro aviso de propiedad
intelectual presente en el Software o en su documentación.

3.6. **Creación de obras derivadas.** Crear obras derivadas, modificaciones, traducciones o
adaptaciones del Software destinadas a distribución comercial o uso fuera de la Instancia
licenciada.

---

## 4. DURACIÓN Y RENOVACIÓN DE LA SUSCRIPCIÓN

4.1. La Suscripción entra en vigor en la fecha de activación de la Clave de Licencia y tiene
la duración contratada (mensual o anual).

4.2. La Suscripción se renueva automáticamente al inicio de cada período salvo que el
Licenciatario notifique su cancelación con al menos **15 días de antelación** al vencimiento.

4.3. El Licenciante emitirá un token de autorización con validez de **30 días** desde su emisión.
El Software intentará renovar dicho token cada **7 días** mientras la Suscripción esté activa
y el pago al día.

---

## 5. IMPAGO Y SUSPENSIÓN AUTOMÁTICA

5.1. **En caso de impago** de la cuota de Suscripción en la fecha de vencimiento, el Licenciante
se reserva el derecho a no renovar el token de autorización, lo que resultará en la
**suspensión automática y total del funcionamiento del Software** una vez transcurridos los
30 días de validez del último token emitido.

5.2. La suspensión por impago **no supone la rescisión automática del contrato**. El Licenciatario
podrá reactivar el Software regularizando el pago pendiente, momento en el que el Licenciante
emitirá un nuevo token en un plazo de 24 horas hábiles.

5.3. El Licenciante **no será responsable** de ningún perjuicio, pérdida de datos, interrupción
de negocio o daño de cualquier naturaleza derivado de la suspensión del Software por impago.

5.4. Los pagos atrasados devengarán un interés de demora equivalente al tipo legal del dinero
más **8 puntos porcentuales**, calculado desde la fecha de vencimiento.

---

## 6. CLÁUSULAS PENALES ANTI-PLAGIO Y ANTI-ELUSIÓN

**Las infracciones descritas en esta cláusula son especialmente graves y darán lugar a las
sanciones económicas aquí establecidas, sin perjuicio de las acciones civiles y penales
adicionales que procedan.**

6.1. **Elusión del sistema de licencias.** Si el Licenciatario o cualquier tercero, por cuenta
o con conocimiento del Licenciatario, elude, deshabilita o manipula los mecanismos de
verificación de licencia del Software (cláusula 3.2), incurrirá en una **penalización de
30.000 € (treinta mil euros)** por cada instancia en la que se detecte dicha elusión,
pagaderos de forma inmediata a partir de la notificación fehaciente.

6.2. **Distribución no autorizada.** La distribución del Software a terceros sin autorización
(cláusula 3.3) dará lugar a una penalización de **50.000 € (cincuenta mil euros)** por cada
tercero al que se haya facilitado el Software, con independencia de si dicha distribución
ha generado beneficio económico para el infractor.

6.3. **Ingeniería inversa.** El intento documentado de obtención del código fuente mediante
ingeniería inversa, descompilación o cualquier técnica análoga (cláusula 3.1) dará lugar
a una penalización de **20.000 € (veinte mil euros)**, independientemente de si dicho intento
tuvo éxito.

6.4. **Activación múltiple no autorizada.** El uso de una única Clave de Licencia en más de
una Instancia sin autorización (cláusula 3.4) generará una penalización equivalente al
precio de lista de **una licencia por cada Instancia adicional detectada, multiplicado por
tres (3)**, como mínimo de **5.000 €** por Instancia.

6.5. Las penalidades establecidas en esta cláusula son acumulativas entre sí y compatibles
con la reclamación de daños y perjuicios adicionales que excedan dichos importes. El
Licenciante tendrá derecho a emplear evidencias técnicas (registros del Servidor de Licencias,
análisis forense del Software, etc.) como prueba ante los tribunales competentes.

6.6. El Licenciatario acepta expresamente que las penalidades previstas en esta cláusula son
proporcionales al valor del Software y al perjuicio causado al Licenciante, y que no podrán
ser consideradas abusivas o desproporcionadas en el marco del artículo 1154 del Código Civil
español ni de normativa análoga.

---

## 7. PROPIEDAD INTELECTUAL

7.1. El Software, incluyendo su diseño, arquitectura, código fuente, bytecode, algoritmos,
documentación y cualquier obra derivada, es propiedad exclusiva del Licenciante y está
protegido por la Ley de Propiedad Intelectual (Real Decreto Legislativo 1/1996), la Directiva
2009/24/CE sobre protección jurídica de programas de ordenador, y demás legislación aplicable
en materia de propiedad intelectual e industrial.

7.2. La presente licencia no transfiere al Licenciatario ningún derecho de propiedad sobre
el Software. El Licenciatario únicamente adquiere el derecho de uso conforme a los términos
aquí establecidos.

7.3. Las marcas, logotipos y nombres comerciales del Licenciante son marcas registradas o
en proceso de registro. El Licenciatario no podrá utilizarlos sin autorización expresa.

---

## 8. CONFIDENCIALIDAD

8.1. El Licenciatario reconoce que el Software contiene información confidencial y secretos
comerciales del Licenciante. El Licenciatario se compromete a:

- Mantener la confidencialidad del Software y no divulgar su contenido a terceros.
- Adoptar medidas de seguridad razonables para proteger el Software de accesos no autorizados.
- Notificar inmediatamente al Licenciante si tiene conocimiento de cualquier uso no autorizado
  o violación de seguridad.

8.2. La obligación de confidencialidad subsistirá **5 años** después de la terminación del
contrato por cualquier causa.

---

## 9. EXCLUSIÓN DE GARANTÍAS

9.1. El Software se proporciona **"tal cual" (AS IS)**, sin garantías de ningún tipo, expresas
o implícitas, incluyendo pero no limitado a las garantías implícitas de comerciabilidad,
idoneidad para un propósito particular y no infracción.

9.2. El Licenciante no garantiza que el Software sea ininterrumpido, libre de errores, ni que
los defectos sean corregidos en un plazo determinado. El Licenciatario asume la totalidad
del riesgo en cuanto a la calidad y rendimiento del Software.

9.3. El Licenciante no garantiza la compatibilidad del Software con versiones futuras de Odoo,
del sistema operativo, ni con módulos de terceros.

---

## 10. LIMITACIÓN DE RESPONSABILIDAD

10.1. En la máxima medida permitida por la ley aplicable, el Licenciante **no será responsable**
bajo ninguna circunstancia de daños indirectos, incidentales, especiales, consecuentes o
punitivos, incluyendo pero no limitado a pérdida de beneficios, pérdida de datos, interrupción
de negocio o daños a la reputación, aunque el Licenciante haya sido advertido de la posibilidad
de tales daños.

10.2. La responsabilidad total del Licenciante frente al Licenciatario por cualquier causa,
bajo cualquier teoría legal, **no excederá del importe total pagado por el Licenciatario
al Licenciante en los 12 meses anteriores al evento que originó la reclamación**.

---

## 11. TERMINACIÓN

11.1. El Licenciante podrá resolver este contrato de forma inmediata, sin preaviso, en caso de:

- Incumplimiento de cualquiera de las cláusulas 3 (Restricciones) o 6 (Cláusulas penales).
- Concurso de acreedores, insolvencia o liquidación del Licenciatario.
- Uso del Software para fines ilegales o contrarios a la normativa vigente.

11.2. Tras la terminación del contrato, el Licenciatario deberá:

- Cesar inmediatamente el uso del Software.
- Desinstalar el Software de todos los sistemas.
- Destruir todas las copias en su poder, incluidas las de seguridad.
- Certificar por escrito al Licenciante, si este lo solicita, que se ha cumplido lo anterior.

11.3. La terminación del contrato no exime al Licenciatario del pago de las penalidades
devengadas ni de las cuotas pendientes de abono.

---

## 12. PROTECCIÓN DE DATOS

12.1. El Software procesa datos de la empresa del Licenciatario almacenados en su instancia
de Odoo. El Licenciante **no accede, almacena ni procesa** datos del Licenciatario salvo
los estrictamente necesarios para la validación de licencias (UUID de instancia, versión
del módulo, fecha de última validación).

12.2. El tratamiento de datos de licencia se realiza conforme al Reglamento (UE) 2016/679
(RGPD) y la Ley Orgánica 3/2018 (LOPDGDD). Más información en la Política de Privacidad
del Licenciante disponible en https://www.uniasser.com/privacidad.

---

## 13. LEY APLICABLE Y JURISDICCIÓN

13.1. Este contrato se rige por el **derecho español**, con exclusión de sus normas de conflicto
de leyes.

13.2. Las partes se someten expresamente a la **jurisdicción de los Juzgados y Tribunales de
Barcelona** (España), con renuncia expresa a cualquier otro fuero que pudiera corresponderles,
para la resolución de cualquier controversia derivada de este contrato.

13.3. Con carácter previo a la vía judicial, las partes se comprometen a intentar resolver
las discrepancias mediante **mediación** conforme a la Ley 5/2012 de mediación en asuntos
civiles y mercantiles. Si la mediación no resolviera la controversia en 30 días, quedará
expedita la vía judicial.

---

## 14. DISPOSICIONES GENERALES

14.1. **Integridad del contrato.** Este contrato constituye el acuerdo completo entre las partes
respecto a su objeto y reemplaza cualquier acuerdo o entendimiento previo, oral o escrito.

14.2. **Modificaciones.** El Licenciante se reserva el derecho de modificar los términos de
este contrato. Las modificaciones se notificarán con 30 días de antelación mediante email
a la dirección registrada del Licenciatario. El uso continuado del Software tras la notificación
implica la aceptación de los nuevos términos.

14.3. **Divisibilidad.** Si alguna disposición de este contrato fuera declarada nula o
inaplicable, el resto del contrato permanecerá en vigor en su totalidad.

14.4. **Renuncia.** La no exigencia por el Licenciante de cualquier derecho o remedio en un
momento dado no implica renuncia a exigirlo en el futuro.

14.5. **Cesión.** El Licenciatario no podrá ceder este contrato ni los derechos derivados del
mismo sin el consentimiento previo y por escrito del Licenciante. El Licenciante podrá ceder
este contrato libremente, incluso en caso de fusión, adquisición o venta de activos.

---

## 15. ACEPTACIÓN

Al instalar, activar o utilizar el Software, el Licenciatario declara:

1. Haber leído y comprendido íntegramente este contrato.
2. Tener capacidad legal para contratar en nombre propio o de la entidad que representa.
3. Aceptar todos los términos y condiciones aquí establecidos.
4. Ser consciente de que las infracciones descritas en la cláusula 6 generan obligaciones
   económicas inmediatas y exigibles.

---

*© 2024-2026 Uniasser Sistemas SL — Todos los derechos reservados.*
*Registro de la Propiedad Intelectual: [número de registro cuando se obtenga]*
