Name:		configuration-cache-report-fixtures
Version:	1.36
Release:	1
Summary:	Reader for Gradle configuration cache HTML reports
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/gradle/configuration-cache-report
# configuration-cache-report commit 149a37caad31, fixtures module, version 1.36.
Source0:	configuration-cache-report-fixtures-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-time-instant)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-serialization-core)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-serialization-json)
BuildRequires:	mvn(org.jetbrains:annotations)
BuildRequires:	mvn(org.gradle.buildtool.internal:configuration-cache-report)

%description
org.gradle.buildtool.internal:configuration-cache-report-fixtures %{version}.
HtmlReportDataReader from commit 149a37caad31, compiled with kotlinc 2.0.21.
It reads the JSON script elements that HtmlReportWriter emits.

%prep
%autosetup -n configuration-cache-report-fixtures-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
JSON=%{_javadir}/kotlinx-serialization-json.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
REPORT=%{_javadir}/configuration-cache-report.jar
test -s "$STDLIB"
test -s "$INSTANT"
test -s "$CORE"
test -s "$JSON"
test -s "$ANN"
test -s "$REPORT"
mkdir -p classes
find src -name '*.kt' | sort > sources.list
test "$(wc -l < sources.list)" -eq 1
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-cp "$STDLIB:$INSTANT:$CORE:$JSON:$ANN:$REPORT" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 2
test -s classes/org/gradle/problems/internal/report/fixtures/HtmlReportDataReader.class
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: configuration.cache.report.fixtures' > manifest.mf
jar cfm configuration-cache-report-fixtures.jar manifest.mf -C classes .
jar i configuration-cache-report-fixtures.jar
desc=$(jar --describe-module --file configuration-cache-report-fixtures.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'configuration.cache.report.fixtures automatic'
cat > configuration-cache-report-fixtures.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.gradle.buildtool.internal</groupId>
  <artifactId>configuration-cache-report-fixtures</artifactId>
  <version>%{version}</version>
  <name>configuration-cache-report-fixtures</name>
  <description>Reader for Gradle configuration cache HTML reports</description>
  <url>https://github.com/gradle/configuration-cache-report</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.gradle.buildtool.internal</groupId>
      <artifactId>configuration-cache-report</artifactId>
      <version>%{version}</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact configuration-cache-report-fixtures.pom:configuration-cache-report-fixtures.jar \
	--file-name configuration-cache-report-fixtures \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.gradle.buildtool.internal/configuration-cache-report-fixtures.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "configuration-cache-report-fixtures"' "$idx"
test -s %{buildroot}%{_javadir}/configuration-cache-report-fixtures.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/configuration-cache-report-fixtures.jar
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
JSON=%{_javadir}/kotlinx-serialization-json.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
REPORT=%{_javadir}/configuration-cache-report.jar
test -s "$JAR"
mkdir -p check
cat > check/Probe.kt << 'EOF'
import org.gradle.problems.internal.report.HtmlReportWriter
import org.gradle.problems.internal.report.fixtures.HtmlReportDataReader
import org.gradle.problems.internal.report.model.JsConfigurationCacheSummary
import java.io.File

fun main() {
    val summary = JsConfigurationCacheSummary(
        cacheAction = "stored",
        documentationLink = "https://docs.gradle.org",
        totalProblemCount = 2,
        uniqueProblemCount = 2,
        overflownProblemCount = 0
    )
    val file = File("check/report.html")
    file.writer().use { w ->
        val report = HtmlReportWriter(w)
        report.beginHtmlReport()
        report.endHtmlReport(summary)
    }
    val reader = HtmlReportDataReader(file)
    val diag = reader.readDiagnosticsJson()
    val sum = reader.readSummaryJson()
    if (!diag.contains("[")) error("diag")
    if (!sum.contains("stored")) error("sum")
    println("configuration_cache_report_fixtures_ok " + diag.trim().length + " " + summary.totalProblemCount)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-cp "$JAR:$REPORT:$STDLIB:$INSTANT:$CORE:$JSON:$ANN" -d check/out check/Probe.kt
java -cp "check/out:$JAR:$REPORT:$STDLIB:$INSTANT:$CORE:$JSON:$ANN" ProbeKt > check/out.txt
cat check/out.txt
grep -F -qx 'configuration_cache_report_fixtures_ok 3 2' check/out.txt

%files -f .mfiles
%license LICENSE
