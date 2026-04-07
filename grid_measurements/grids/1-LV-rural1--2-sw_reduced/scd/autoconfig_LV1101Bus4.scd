<?xml version='1.0' encoding='utf-8'?>
<SCL xsd="http://www.w3.org/2001/XMLSchema" xsi="http://www.w3.org/2001/XMLSchema-instance" version="2007" revision="B" xmlns="http://www.iec.ch/61850/2003/SCL">
  <Header id="" desc="Data integration level for node LV1101Bus4" type="dLSS" />
  <Substation name="Substation1" desc="Data modeling and integration of LV1101Bus4">
    <VoltageLevel name="NE1">
      <Voltage unit="V">400.0</Voltage>
      <Bay name="Data integration node LV1101Bus4">
        <Function name="DataIntegrator1" type="DataIntegrator">
          <Private type="ie3.iAutomate.SCL.PrivateContents.tDataIntegratorConfiguration">
            <DataIntegratorConfiguration db_access_path="database.ini" xmlns="http://www.ie3.e-technik.tu-dortmund.de/ie3.iAutomate.SCL.PrivateContents" />
          </Private>
        </Function>
      </Bay>
      <Bay name="dLSS node LV1101Bus4, transformer" />
      <Bay name="dLSS bay Q01, feeder" />
      <Bay name="dLSS bay Q02, feeder" />
      <Bay name="dLSS bay Q03, transformer" />
    </VoltageLevel>
  </Substation>
  <Communication>
    <SubNetwork name="LSS-LAN" type="Modbus-IP">
      <ConnectedAP iedName="Data integration node LV1101Bus4" apName="AccessPoint1">
        <Address>
          <P type="tP_IP">129.217.187.132</P>
          <P type="tP_IP-GATEWAY">0.0.0.0</P>
          <P type="tP_IP-SUBNET">255.255.255.0</P>
          <P type="tP_OSI-PSEL">00000001</P>
          <P type="tP_OSI-SSEL">0001</P>
          <P type="tP_OSI-TSEL">0001</P>
        </Address>
      </ConnectedAP>
      <ConnectedAP iedName="dLSS node LV1101Bus4, transformer" apName="AccessPoint1">
        <Address>
          <P type="tP_IP">129.217.202.43</P>
          <P type="PORT">502</P>
          <P type="Unit-ID">99</P>
          <P type="tP_IP-GATEWAY">0.0.0.0</P>
          <P type="tP_IP-SUBNET">255.255.255.0</P>
          <P type="tP_OSI-PSEL">00000001</P>
          <P type="tP_OSI-SSEL">0001</P>
          <P type="tP_OSI-TSEL">0001</P>
        </Address>
      </ConnectedAP>
      <ConnectedAP iedName="dLSS bay Q01, feeder" apName="AccessPoint1">
	    <!-- feeder to node 7 --> 
        <Address>
          <P type="tP_IP">129.217.202.43</P>
          <P type="PORT">502</P>
          <P type="Unit-ID">13</P>
          <P type="tP_IP-GATEWAY">0.0.0.0</P>
          <P type="tP_IP-SUBNET">255.255.255.0</P>
          <P type="tP_OSI-PSEL">00000001</P>
          <P type="tP_OSI-SSEL">0001</P>
          <P type="tP_OSI-TSEL">0001</P>
        </Address>
      </ConnectedAP>
      <ConnectedAP iedName="dLSS bay Q02, feeder" apName="AccessPoint1">
        <!-- feeder to node 2 -->
		<Address>
          <P type="tP_IP">129.217.202.43</P>
          <P type="PORT">502</P>
          <P type="Unit-ID">12</P>
          <P type="tP_IP-GATEWAY">0.0.0.0</P>
          <P type="tP_IP-SUBNET">255.255.255.0</P>
          <P type="tP_OSI-PSEL">00000001</P>
          <P type="tP_OSI-SSEL">0001</P>
          <P type="tP_OSI-TSEL">0001</P>
        </Address>
      </ConnectedAP>
      <ConnectedAP iedName="dLSS bay Q03, transformer" apName="AccessPoint1">
        <Address>
          <P type="tP_IP">129.217.202.43</P>
          <P type="PORT">502</P>
          <P type="Unit-ID">11</P>
          <P type="tP_IP-GATEWAY">0.0.0.0</P>
          <P type="tP_IP-SUBNET">255.255.255.0</P>
          <P type="tP_OSI-PSEL">00000001</P>
          <P type="tP_OSI-SSEL">0001</P>
          <P type="tP_OSI-TSEL">0001</P>
        </Address>
      </ConnectedAP>
    </SubNetwork>
  </Communication>
  <IED desc="Data fetcher and preprocessor" name="Data integration node LV1101Bus4">
    <Services>
      <DynAssociation />
      <GetDirectory />
      <GetDataObjectDefinition />
      <GetDataSetValue />
      <DataSetDirectory />
      <ConfDataSet max="4" />
      <GetCBValues />
      <ConfLogControl max="1" />
      <ReportSettings />
      <GSESettings />
      <GOOSE max="2" />
      <FileHandling />
      <ConfLNs />
    </Services>
    <AccessPoint name="AccessPoint1">
      <Server desc="Server">
        <Authentication />
        <LDevice desc="DataIntegrator1" inst="LDevice1">
          <LN0 lnType="DT_LNO" lnClass="LLN0" inst="" />
          <LN desc="Physical Device Information" lnType="DT_LPHD" lnClass="LPHD" inst="1" />
        </LDevice>
        <LDevice desc="operational_limit_monitoring" inst="LDevice1">
          <LN0 lnType="DT_LNO" lnClass="LLN0" inst="" />
          <LN desc="Threshold Detection" prefix="voltage_limit_" lnType="DT_FLIM" lnClass="FLIM" inst="1" />
          <LN desc="Threshold Detection" prefix="current_limit_" lnType="DT_FLIM" lnClass="FLIM" inst="1" />
        </LDevice>
      </Server>
    </AccessPoint>
    <Accesspoint name="ClientAP">
      <LN desc="Telecontrol Interface" lnType="DT_ITCI" lnClass="ITCI" inst="1" />
    </Accesspoint>
  </IED>
  <IED desc="digital local substation transformer" name="dLSS node LV1101Bus4, transformer" />
  <IED desc="digital local substation feeder" name="dLSS bay Q01, feeder">
    <Services>
      <DynAssociation />
      <GetDirectory />
      <GetDataObjectDefinition />
      <GetDataSetValue />
      <DataSetDirectory />
      <ConfDataSet max="4" />
      <GetCBValues />
      <ConfLogControl max="1" />
      <ReportSettings />
      <GSESettings />
      <GOOSE max="2" />
      <FileHandling />
      <ConfLNs />
    </Services>
    <AccessPoint name="AccessPoint1">
      <Server desc="Server">
        <Authentication />
        <LDevice desc="Cubicle Q01, Leitungsfeld" inst="Q01">
          <LN0 lnType="DT_LNO" lnClass="LLN0" inst="">
            <DataSet name="Q01_measurements" />
            <ReportControl name="Cubicle Q01, Leitungsfeld_report" datSet="Q01_measurements" intgPd="15000" rptID="Cubicle Q01, Leitungsfeld_report" confRev="1">
              <TrgOps period="true" />
              <RptEnabled>
                <ClientLN iedName="Data integration node LV1101Bus4" ldInst="None" lnClass="ITCI" lnInst="1" />
              </RptEnabled>
            </ReportControl>
          </LN0>
          <LN desc="Measurement" prefix="Q01_" lnType="DT_MMXU" lnClass="MMXU" inst="1">
            <DOI name="W">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=1;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=3;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=5;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotW">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=7;T=float)" />
              </SDI>
            </DOI>
            <DOI name="A">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=9;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=11;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=13;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="Hz">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=15;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PhV">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=17;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=19;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=21;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="VAr">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=23;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=25;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=27;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVAr">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=29;T=float)" />
              </SDI>
            </DOI>
            <DOI name="VA">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=31;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=33;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=35;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVA">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=37;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PF">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=39;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=41;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=43;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotPF">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=45;T=float)" />
              </SDI>
            </DOI>
          </LN>
          <LN desc="Measurement" prefix="Q01_" lnType="DT_STMP" lnClass="STMP" inst="1" />
        </LDevice>
      </Server>
    </AccessPoint>
  </IED>
  <IED desc="digital local substation feeder" name="dLSS bay Q02, feeder">
    <Services>
      <DynAssociation />
      <GetDirectory />
      <GetDataObjectDefinition />
      <GetDataSetValue />
      <DataSetDirectory />
      <ConfDataSet max="4" />
      <GetCBValues />
      <ConfLogControl max="1" />
      <ReportSettings />
      <GSESettings />
      <GOOSE max="2" />
      <FileHandling />
      <ConfLNs />
    </Services>
    <AccessPoint name="AccessPoint1">
      <Server desc="Server">
        <Authentication />
        <LDevice desc="Cubicle Q02, Leitungsfeld" inst="Q02">
          <LN0 lnType="DT_LNO" lnClass="LLN0" inst="">
            <DataSet name="Q02_measurements" />
            <ReportControl name="Cubicle Q02, Leitungsfeld_report" datSet="Q02_measurements" intgPd="15000" rptID="Cubicle Q02, Leitungsfeld_report" confRev="1">
              <TrgOps period="true" />
              <RptEnabled>
                <ClientLN iedName="Data integration node LV1101Bus4" ldInst="None" lnClass="ITCI" lnInst="1" />
              </RptEnabled>
            </ReportControl>
          </LN0>
          <LN desc="Measurement" prefix="Q02_" lnType="DT_MMXU" lnClass="MMXU" inst="1">
            <DOI name="W">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=1;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=3;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=5;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotW">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=7;T=float)" />
              </SDI>
            </DOI>
            <DOI name="A">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=9;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=11;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=13;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="Hz">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=15;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PhV">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=17;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=19;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=21;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="VAr">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=23;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=25;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=27;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVAr">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=29;T=float)" />
              </SDI>
            </DOI>
            <DOI name="VA">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=31;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=33;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=35;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVA">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=37;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PF">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=39;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=41;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=43;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotPF">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=45;T=float)" />
              </SDI>
            </DOI>
          </LN>
          <LN desc="Measurement" prefix="Q02_" lnType="DT_STMP" lnClass="STMP" inst="1" />
        </LDevice>
      </Server>
    </AccessPoint>
  </IED>
  <IED desc="digital local substation feeder" name="dLSS bay Q03, transformer">
    <Services>
      <DynAssociation />
      <GetDirectory />
      <GetDataObjectDefinition />
      <GetDataSetValue />
      <DataSetDirectory />
      <ConfDataSet max="4" />
      <GetCBValues />
      <ConfLogControl max="1" />
      <ReportSettings />
      <GSESettings />
      <GOOSE max="2" />
      <FileHandling />
      <ConfLNs />
    </Services>
    <AccessPoint name="AccessPoint1">
      <Server desc="Server">
        <Authentication />
        <LDevice desc="Cubicle Q03, Trafofeld" inst="Q03">
          <LN0 lnType="DT_LNO" lnClass="LLN0" inst="">
            <DataSet name="Q03_measurements" />
            <ReportControl name="Cubicle Q03, Trafofeld_report" datSet="Q03_measurements" intgPd="15000" rptID="Cubicle Q03, Trafofeld_report" confRev="1">
              <TrgOps period="true" />
              <RptEnabled>
                <ClientLN iedName="Data integration node LV1101Bus4" ldInst="None" lnClass="ITCI" lnInst="1" />
              </RptEnabled>
            </ReportControl>
          </LN0>
          <LN desc="Measurement" prefix="Q03_" lnType="DT_MMXU" lnClass="MMXU" inst="1">
            <DOI name="W">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=1;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=3;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=5;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotW">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=7;T=float)" />
              </SDI>
            </DOI>
            <DOI name="A">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=9;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=11;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=13;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="Hz">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=15;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PhV">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=17;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=19;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=21;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="VAr">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=23;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=25;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=27;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVAr">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=29;T=float)" />
              </SDI>
            </DOI>
            <DOI name="VA">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=31;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=33;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=35;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotVA">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=37;T=float)" />
              </SDI>
            </DOI>
            <DOI name="PF">
              <SDI name="phsA">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=39;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsB">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=41;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
              <SDI name="phsC">
                <SDI name="cVal">
                  <SDI name="mag">
                    <DAI name="f" sAddr="Modbus(HoldingRegister=43;T=float)" />
                  </SDI>
                </SDI>
              </SDI>
            </DOI>
            <DOI name="TotPF">
              <SDI name="mag">
                <DAI name="f" sAddr="Modbus(HoldingRegister=45;T=float)" />
              </SDI>
            </DOI>
          </LN>
          <LN desc="Measurement" prefix="Q03_" lnType="DT_STMP" lnClass="STMP" inst="1" />
        </LDevice>
      </Server>
    </AccessPoint>
  </IED>
  <DataTypeTemplates>
    <LNodeType id="DT_MMXU" desc="Measurement" lnClass="MMXU">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="TotW" type="DT_MV" />
      <DO name="TotVAr" type="DT_MV" />
      <DO name="TotVA" type="DT_MV" />
      <DO name="TotPF" type="DT_MV" />
      <DO name="Hz" type="DT_MV" />
      <DO name="PhV" type="DT_WYE" />
      <DO name="A" type="DT_WYE" />
      <DO desc="Phase active power (P)" name="W" type="DT_WYE" />
      <DO desc="Phase reactive power (Q)" name="VAr" type="DT_WYE" />
      <DO desc="Phase apparent power (S)" name="VA" type="DT_WYE" />
      <DO desc="Phase power factor" name="PF" type="DT_WYE" />
      <DO desc="Phase impedance" name="Z" type="DT_WYE" />
      <DO name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
      <DO desc="Calculation Method" name="ClcMth" type="DT_ENG_ClcMth" />
      <DO desc="Power Factor Sign" name="PFSign" type="DT_ENG_PF_Sign" />
    </LNodeType>
    <LNodeType id="DT_MMTR" desc="Energy in three-phase systems" lnClass="MMTR">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="TotVAh" type="DT_BCR" />
      <DO name="TotWh" type="DT_BCR" />
      <DO name="TotVArh" type="DT_BCR" />
      <DO name="SupWh" type="DT_BCR" />
      <DO name="SupVArh" type="DT_BCR" />
      <DO name="DmdWh" type="DT_BCR" />
      <DO name="DmdVArh" type="DT_BCR" />
      <DO name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
      <DO desc="Calculation Method" name="ClcMth" type="DT_ENG_ClcMth" />
    </LNodeType>
    <LNodeType id="DT_FLIM" desc="Control function output limitation" lnClass="FLIM">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="HiLim" type="DT_SPS" />
      <DO name="LoLim" type="DT_SPS" />
      <DO name="HiLimSpt" type="DT_ASG" />
      <DO name="LoLimSpt" type="DT_ASG" />
      <DO name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_MMDC" desc="DC measurement" lnClass="MMDC">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="Watt" type="DT_MV" />
      <DO name="Amp" type="DT_MV" />
      <DO name="Vol" type="DT_MV" />
      <DO name="VolPsGnd" type="DT_MV" />
      <DO name="VolNgGnd" type="DT_MV" />
      <DO name="Ris" type="DT_MV" />
      <DO name="RisPsGnd" type="DT_MV" />
      <DO name="RisNgGnd" type="DT_MV" />
      <DO name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_MMET" desc="Meteorological information" lnClass="MMET">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Ambient temperature" name="EnvTmp" type="DT_MV" />
      <DO desc="Wet bulb temperature" name="WetBlbTmp" type="DT_MV" />
      <DO desc="Cloud cover level" name="CloudCvr" type="DT_MV" />
      <DO desc="Humidity" name="EnvHum" type="DT_MV" />
      <DO desc="Dew point" name="DewPt" type="DT_MV" />
      <DO desc="Diffuse insolation" name="DffInsol" type="DT_MV" />
      <DO desc="Direct normal insolation" name="DctInsol" type="DT_MV" />
      <DO desc="Daylight duration (time elapsed between sunrise and sunset)" name="DlDur" type="DT_MV" />
      <DO desc="Total horizontal insolation" name="HorInsol" type="DT_MV" />
      <DO desc="Horizontal wind direction" name="HorWdDir" type="DT_MV" />
      <DO desc="Horizontal wind speed" name="HorWdSpd" type="DT_MV" />
      <DO desc="Vertical wind direction" name="VerWdDir" type="DT_MV" />
      <DO desc="Vertical wind speed" name="VerWdSpd" type="DT_MV" />
      <DO desc="Wind gust speed" name="WdGustSpd" type="DT_MV" />
      <DO desc="Barometric pressure" name="EnvPres" type="DT_MV" />
      <DO desc="Rainfall" name="RnFll" type="DT_MV" />
      <DO desc="Density of snowfall" name="SnwDen" type="DT_MV" />
      <DO desc="Temperature of snowfall" name="SnwTmp" type="DT_MV" />
      <DO desc="Snow cover" name="SnwCvr" type="DT_MV" />
      <DO desc="Snowfall" name="SnwFll" type="DT_MV" />
      <DO desc="Water equivalent of snowfall" name="SnwEq" type="DT_MV" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_DPVM" desc="Photovoltaic module characteristics" lnClass="DPVM">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Index into active point of the AV curve" name="AVCrv" type="DT_INS" />
      <DO desc="PV module configuration type" name="MdulCfgTyp" type="DT_ENG_PV_Config" />
      <DO desc="Amp-Volt curve of module at STC" name="MdulAVCrv" type="DT_CSG" />
      <DO desc="Module rated power at watts peak STC" name="MdulWRtg" type="DT_ASG" />
      <DO desc="Module rated power as watts peak at 200 W/m2" name="MdulW200Rtg" type="DT_ASG" />
      <DO desc="Module voltage at max power at STC" name="MaxMdulV" type="DT_ASG" />
      <DO desc="Module current at max power at STC" name="MaxMdulA" type="DT_ASG" />
      <DO desc="Module open circuit voltage (Voc at STC)" name="MdulOpnCctV" type="DT_ASG" />
      <DO desc="Module short circuit current (Isc at STC)" name="MdulSrtCctA" type="DT_ASG" />
      <DO desc="Module power/temperature derate as percent of degrees above 25 ºC" name="MdulWTmpDrt" type="DT_ASG" />
      <DO desc="Module current/temperature derate as percent of degrees above 25 ºC" name="MdulATmpDrt" type="DT_ASG" />
      <DO desc="Module voltage/temperature derate as voltage/degrees above 25 ºC" name="MdulVTmpDrt" type="DT_ASG" />
      <DO desc="Module age derate as percent over time" name="MdulAgeDrtPct" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_DPVA" desc="Photovoltaics array characteristics" lnClass="DPVA">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Assembly type" name="Typ" type="DT_ENG_PV_Assembly" />
      <DO desc="Type of ground connection" name="GndConn" type="DT_ENG_PV_Gnd_Conn" />
      <DO desc="Number of modules per string" name="MdulCnt" type="DT_ING" />
      <DO desc="Number of parallel strings per sub-array" name="StrgCnt" type="DT_ING" />
      <DO desc="Number of parallel sub-arrays per array" name="SubArrCnt" type="DT_ING" />
      <DO desc="Array area" name="ArrArea" type="DT_ASG" />
      <DO desc="Array power rating (watts peak – watts p)" name="ArrWRtg" type="DT_ASG" />
      <DO desc="Assembly fixed tilt – degrees from horizontal" name="Tilt" type="DT_ASG" />
      <DO desc="Assembly azimuth – degrees from true north" name="Azi" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_DINV" desc="Inverter Characteristics" lnClass="DINV">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Alarm: Loss of AC power" name="InvACLosAlm" type="DT_SPS" />
      <DO desc="Alarm: Loss of DC power" name="InvDCLosAlm" type="DT_SPS" />
      <DO desc="Alarm: Loss of grid power" name="InvGriLosAlm" type="DT_SPS" />
      <DO desc="Alarm: Inverter contactor switch open or closed" name="InvSwAlm" type="DT_SPS" />
      <DO desc="Inverter stand-by is active" name="Stdby" type="DT_SPS" />
      <DO desc="DC current level is sufficient" name="CurLev" type="DT_SPS" />
      <DO desc="Inverter manual shutdown command received" name="InvManStopSt" type="DT_SPS" />
      <DO desc="Active power setpoint" name="WSpt" type="DT_APC" />
      <DO desc="Reactive power setpoint" name="VArSpt" type="DT_APC" />
      <DO desc="Type of inverter switch" name="InvSwTyp" type="DT_ENG_Inv_Switch_Kind" />
      <DO desc="Inverter control source" name="InvCtlSrc" type="DT_ENG_Inv_Ctl_Src" />
      <DO desc="Rated active power of the inverter" name="WRtg" type="DT_ASG" />
      <DO desc="Continuous apparent power capability of the inverter" name="VARtg" type="DT_ASG" />
      <DO desc="Nominal switching frequency" name="SwHz" type="DT_ASG" />
      <DO desc="Continuous apparent power capability of the inverter" name="VARtg" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_SINV" desc="Inverter condition monitoring" lnClass="SINV">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Enclosure temperature" name="EnclTmp" type="DT_MV" />
      <DO desc="Heat sink temperature" name="HeatSinkTmp" type="DT_MV" />
      <DO desc="Transformer temperature" name="TrfTmp" type="DT_MV" />
      <DO desc="Measured fan speed" name="FanSpd" type="DT_MV" />
      <DO desc="Upper temperature status" name="TmpHiAlm" type="DT_SPS" />
    </LNodeType>
    <LNodeType id="DT_DGEN" desc="DER generating unit" lnClass="DGEN">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Synchronization status of DER Generator unit" name="GnSynSt" type="DT_ENS_DER_Sync_Stat" />
      <DO desc="Current state of DER operation" name="DEROpSt" type="DT_ENS_DER_State_Kind" />
      <DO desc="Maximum power the generator could output" name="CnstWMax" type="DT_MV" />
      <DO desc="Total energy generated" name="GnEnTot" type="DT_MV" />
      <DO desc="Energy generated in period since last reset" name="GnEnPer" type="DT_MV" />
      <DO desc="Percentage of active power generated from renewables" name="RenWPct" type="DT_MV" />
      <DO desc="Percentage of reactive power generated from renewables" name="RenVArPct" type="DT_MV" />
      <DO desc="Total amount of reactive power without impacting active power" name="VArTot" type="DT_MV" />
      <DO desc="Total amount of absorbable reactive power without impacting active power" name="AvarTot" type="DT_MV" />
      <DO desc="Total amount of injectable reactive power without impacting active power" name="IvarTot" type="DT_MV" />
      <DO desc="Actual percentage of apparent power output based on VAMax" name="VAPct" type="DT_MV" />
      <DO desc="Available capacity for increasing active power output" name="AvlUpW" type="DT_MV" />
      <DO desc="Available capacity for decreasing active power output" name="AvlDnW" type="DT_MV" />
      <DO desc="Active power setpoint" name="WSpt" type="DT_APC" />
      <DO desc="Reactive power setpoint" name="VArSpt" type="DT_APC" />
      <DO desc="Reference to DER Unit LN possibly associated to this generic model LN" name="DERUnit" type="DT_ORG" />
      <DO desc="Nameplate maximum active power generation" name="WMaxRtg" type="DT_ASG" />
      <DO desc="Nameplate maximum apparent power generation" name="VAMaxRtg" type="DT_ASG" />
      <DO desc="Nameplate maximum reactive power generation" name="VArMaxRtg" type="DT_ASG" />
      <DO desc="Nameplate maximum absorbable reactive power" name="AvarMaxRtg" type="DT_ASG" />
      <DO desc="Nameplate maximum injectable reactive power" name="IvarMaxRtg" type="DT_ASG" />
      <DO desc="Maximum current rating under nominal voltage and power factor" name="AMaxRtg" type="DT_ASG" />
      <DO desc="Maximum voltage rating" name="VMaxRtg" type="DT_ASG" />
      <DO desc="Minimum voltage rating" name="VMinRtg" type="DT_ASG" />
      <DO desc="Minimum continuous active power generation rating" name="ConsWMinRtg" type="DT_ASG" />
      <DO desc="Maximum continuous active power generation rating" name="ConsWMaxRtg" type="DT_ASG" />
      <DO desc="Maximum generation active power ramp up rating" name="WRpuMaxRtg" type="DT_ASG" />
      <DO desc="Maximum generation active power ramp down rating" name="WRpdMaxRtg" type="DT_ASG" />
      <DO desc="Setting for maximum active power" name="WMax" type="DT_ASG" />
      <DO desc="Default ramp rate for changes in active power, percentage of WMax/s" name="WRmp" type="DT_ASG" />
      <DO desc="Setting for maximum reactive power" name="VArMax" type="DT_ASG" />
      <DO desc="Setting for maximum absorbable reactive power" name="AvarMax" type="DT_ASG" />
      <DO desc="Setting for maximum injectable reactive power" name="IvarMax" type="DT_ASG" />
      <DO desc="Setting for maximum voltage operational rating" name="VMax" type="DT_ASG" />
      <DO desc="Setting for minimum voltage operational rating" name="VMin" type="DT_ASG" />
      <DO desc="Setting for maximum operational current rating under nominal voltage and power factor" name="AMax" type="DT_ASG" />
      <DO desc="Setting for maximum apparent power while generating" name="VAMax" type="DT_ASG" />
      <DO desc="Setting for maximum absorbable apparent power" name="AvaMax" type="DT_ASG" />
      <DO desc="Setting for maximum injectable apparent power" name="IvaMax" type="DT_ASG" />
      <DO desc="Reference for reactive power setpoints, selects active setpoints" name="VArSptRef" type="DT_ENG_Reactive_Power_kind" />
      <DO desc="Maximum reactive power absorbed in case of zero active power" name="AvarZerWMax" type="DT_ASG" />
      <DO desc="Maximum reactive power injected in case of zero active power" name="IvarZerWMax" type="DT_ASG" />
      <DO desc="Phase type of electrical connection of DER" name="PhsConnTyp" type="DT_ENG_Phasekind" />
      <DO desc="Type of DER" name="DERTyp" type="DT_ENG_DERUnitkind" />
      <DO desc="Maximum temperature rating" name="TmpMaxRtg" type="DT_ASG" />
      <DO desc="Rated nominal frequency for usage of the DER" name="HzNomRtg" type="DT_ASG" />
      <DO desc="Rated minimal frequency for usage of the DER" name="HzMinRtg" type="DT_ASG" />
      <DO desc="Rated maximal frequency for usage of the DER" name="HzMaxRtg" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_GGIO" desc="Generic Process I/O" lnClass="GGIO">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Local or remote key" name="LocKey" type="DT_SPS" />
      <DO desc="Local control behaviour" name="Loc" type="DT_SPS" />
      <DO desc="Integer status input" name="IntIn1" type="DT_SPS" />
      <DO desc="General single alarm" name="Alm1" type="DT_SPS" />
      <DO desc="General single warning" name="Wrn1" type="DT_SPS" />
      <DO desc="General indication (binary input)" name="Ind1" type="DT_SPS" />
      <DO desc="Analogue input" name="AnIn1" type="DT_MV" />
      <DO desc="Controllable analogue output" name="AnOut1" type="DT_APC" />
      <DO desc="Counter, resettable" name="CntRs1" type="DT_BCR" />
      <DO desc="Resettable operation counter" name="OpCntRs" type="DT_INC" />
      <DO desc="Switching authority at station level" name="LocSta" type="DT_SPC" />
      <DO desc="Single point controllable status output" name="SPCSO1" type="DT_SPC" />
      <DO desc="Double point controllable status output" name="DPCSO1" type="DT_DPC" />
      <DO desc="Integer status controllable status output" name="ISCSO1" type="DT_INC" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_DPVC" desc="remote monitoring and control of PV array controller" lnClass="DPVC">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Array control mode status" name="PVCtlSt" type="DT_ENS_PVControlStateKind" />
      <DO desc="Control the power output of the array" name="ArrModCtl" type="DT_ENC_PVArrayControlModeKind" />
      <DO desc="Peak power tracker reference voltage" name="PVCtlSt" type="DT_ASG" />
      <DO desc="Power tracker wake-up voltage" name="TrkWkupV" type="DT_ASG" />
      <DO desc="Power tracker update rate" name="TrkRte" type="DT_ING" />
      <DO desc="Voltage perturbation step of power tracker" name="TrkVStep" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_STMP" desc="Temperature supervision" lnClass="STMP">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Temperature rate change alarm status" name="Alm" type="DT_SPS" />
      <DO desc="Temperature rate change alarm status" name="RteAlm" type="DT_SPS" />
      <DO desc="Measured Temperature" name="Tmp" type="DT_MV" />
      <DO desc="Rate of Temperature change" name="TmpRte" type="DT_MV" />
      <DO desc="Temperature exceeded Trip Setting" name="Trip" type="DT_SPS" />
      <DO desc="Temperature exceeded Rate of Trip Setting" name="RteTrip" type="DT_SPS" />
      <DO desc="Temperature alarm trigger status setting" name="AlmSet" type="DT_ASG" />
      <DO desc="Temperature rate alarm trigger status setting" name="RteAlmSet" type="DT_ASG" />
      <DO desc="Temperature trip level setting" name="TripSet" type="DT_ASG" />
      <DO desc="Temperature rate trip level setting" name="RteTripSet" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
    </LNodeType>
    <LNodeType id="DT_XSWI" desc="Circuit Switch" lnClass="XSWI">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="Loc" type="DT_SPS" />
      <DO name="LocSta" type="DT_SPC" />
      <DO name="OpCnt" type="DT_INS" />
      <DO name="SwTyp" type="DT_ENS_SwTyp" />
      <DO name="Pos" type="DT_DPC" />
      <DO name="BlkOpn" type="DT_SPC" />
      <DO name="BlkCls" type="DT_SPC" />
      <DO name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_TCTR" desc="Current Transformer" lnClass="TCTR">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="AmpSv" type="DT_SAV" />
      <DO desc="Rated current" name="ARtg" type="DT_ASG" />
      <DO desc="Winding ratio of an external current transformer (transducer) if applicable" name="Rat" type="DT_ASG" />
      <DO desc="Current phasor angle correction of an external current transformer" name="AngCor" type="DT_ASG" />
      <DO name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_TVTR" desc="Voltage Transformer" lnClass="TVTR">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO name="VolSv" type="DT_SAV" />
      <DO desc="Rated voltage" name="VRtg" type="DT_ASG" />
      <DO desc="Winding ratio of external voltage transformer (transducer) if applicable" name="Rat" type="DT_ASG" />
      <DO desc="Voltage phasor angle correction of external voltage transformer" name="AngCor" type="DT_ASG" />
      <DO name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_LN0" desc="Logical Node Zero" lnClass="LLN0">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Mode" name="Mod" type="DT_ENC_Mod" />
      <DO desc="Name plate" name="NamPlt" type="DT_LPL" />
      <DO desc="Health" name="Health" type="DT_ENS_Health" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_LPHD" desc="Physical Device Information" lnClass="LPHD">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Physical device name plate" name="PhyNam" type="DT_DPL" />
      <DO desc="Physical device health" name="PhyHealth" type="DT_ENS_Health" />
      <DO desc="Indicates if this LN is a proxy" name="Proxy" type="DT_SPS" />
    </LNodeType>
    <LNodeType id="DT_GAPC" desc="Generic Automatic Process Control" lnClass="GAPC">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Local or remote key" name="LocKey" type="DT_SPS" />
      <DO desc="Local control behaviour" name="Loc" type="DT_SPS" />
      <DO desc="Automatic operation" name="Auto" type="DT_SPC" />
      <DO desc="Start" name="Str1" type="DT_ACD" />
      <DO desc="Operate" name="Op1" type="DT_ACT" transient="true" />
      <DO desc="Generic single alarm" name="Alm1" type="DT_SPS" />
      <DO desc="Generic single warning" name="Wrn1" type="DT_SPS" />
      <DO desc="Generic single indication" name="Ind1" type="DT_SPS" />
      <DO desc="Resettable operation counter" name="OpCntRs" type="DT_INC" />
      <DO desc="Switching authority at station level" name="LocSta" type="DT_SPC" />
      <DO desc="Single point controllable status output" name="SPCSO1" type="DT_SPC" />
      <DO desc="Double point controllable status output" name="DPCSO1" type="DT_DPC" />
      <DO desc="Integer status controllable status output" name="ISCSO1" type="DT_INC" />
      <DO desc="Start value" name="StrVal1" type="DT_ASG" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_ITCI" desc="Telecontrol Interface" lnClass="ITCI">
      <DO desc="Name plate of external equipment" name="EEName" type="DT_DPL" />
      <DO desc="Behaviour" name="Beh" type="DT_ENS_Beh" />
    </LNodeType>
    <LNodeType id="DT_DESE" desc="E-Mobility supply equipment logical node">
      <DO desc="EVSE nameplate" name="EVSENam" type="DT_DPL" />
      <DO desc="Isolation test fault executed before charging has failed" name="IsoTestFlt" type="DT_SPS" />
      <DO desc="Short circuit test fault executed before charging has failed" name="ScTestFlt" type="DT_SPS" />
      <DO desc="Detection of loss of digital communication" name="DigCommLos" type="DT_SPS" />
      <DO desc="Detection of welding condition" name="WldDet" type="DT_SPS" />
      <DO desc="Charging voltage" name="ChaV" type="DT_MV" />
      <DO desc="Charging current" name="ChaA" type="DT_MV" />
      <DO desc="Electric Vehicle supply equipment id as per ISO 15118-2:2014" name="EVSEId" type="DT_VSG" />
      <DO desc="Rated maximum charging power of the EVSE (charging station)" name="ChaPwrRtg" type="DT_ASG" />
      <DO desc="The power that the EVSE requires from the grid" name="ChaPwrTgt" type="DT_ASG" />
      <DO desc="The power that the grid limits the charger to" name="DT_ChaPwrLim" type="DT_ASG" />
      <DO desc="DC charging supported (True means yes)" name="ConnTypDC" type="DT_SPG" />
      <DO desc="True = AC charging supported with n phases" name="ConnTypPhs" type="DT_SPG" />
      <DO desc="Reference to the logical node(s) representing AC charging connections" name="ConnACRef" type="DT_ORG" />
      <DO desc="Reference to the logical node(s) representing DC charging connections" name="ConnDCRef" type="DT_ORG" />
    </LNodeType>
    <LNodeType id="DT_FSPT" desc="Setpoint control function" lnClass="FSPT">
      <DO desc="Deviation alarm trigger status" name="SptDvAlm" type="DT_SPS" />
      <DO desc="Setpoint is raising, represent feedbacks from external devices" name="SptUp" type="DT_SPS" />
      <DO desc="Setpoint is lowering, represent feedbacks from external devices" name="SptDn" type="DT_SPS" />
      <DO desc="True: Setpoint is incrementing when last checked, otherwise it is decrementing" name="DptDir" type="DT_SPS" />
      <DO desc="Status of setpoint ending" name="SptEndSt" type="DT_ENS_SetpointEndKind" />
      <DO desc="State of adjustment process" name="AdjSt" type="DT_ENS_AdjustmentKind" />
      <DO desc="Local control behaviour" name="Loc" type="DT_SPS" />
      <DO desc="Analogue output of this function" name="Out" type="DT_MV" />
      <DO desc="Setpoint value maintained in memory" name="SptMem" type="DT_MV" />
      <DO desc="Operating with a value to initiate the setpoint adjustment to a given diretion" name="SptChg" type="DT_BAC" />
      <DO desc="controllable value of a setpoint" name="SptVal" type="DT_APC" />
      <DO desc="Auomatic operation" name="Auto" type="DT_SPC" />
      <DO desc="Maximum restriction" name="MaxRst" type="DT_ASG" />
      <DO desc="Minimum restriction" name="MinRst" type="DT_ASG" />
      <DO desc="Setpoint deviation at which the alarm trigger status should be active" name="DvAlm" type="DT_ASG" />
    </LNodeType>
    <LNodeType id="DT_DBAT" desc="Battery system monitoring and controlling" lnClass="DBAT">
      <DO desc="State of charge protection of the battery is activated" name="SocPro" type="DT_SPS" />
      <DO desc="If true, batery is charging" name="ChaSt" type="DT_SPS" />
      <DO desc="If true, battery is discharging" name="DschSt" type="DT_SPS" />
      <DO desc="Battery test results" name="BatTestRsl" type="DT_ENS_BatteryTestResultKind" />
      <DO desc="If true, battery DC contactor (switch) is closed, otherwise open" name="DCSwCls" type="DT_SPS" />
      <DO desc="Battery drain DC current" name="Amp" type="DT_MV" />
      <DO desc="Battery DC watts" name="Watt" type="DT_MV" />
      <DO desc="Instantaneous DC current limit on charging" name="ChaAmpLim" type="DT_MV" />
      <DO desc="Effective Ampere-hour operational value, including after degradation" name="EffAhr" type="DT_MV" />
      <DO desc="Instantaneous voltage limit on charging" name="ChaVolLim" type="DT_MV" />
      <DO desc="Instantaneous DC current limit on discharging" name="DschAmpLim" type="DT_MV" />
      <DO desc="Number of strings of cells currently connected" name="CelStrgCnt" type="DT_MV" />
      <DO desc="Available charge capacity to be charged in Amp-hours" name="AvlChaAhr" type="DT_MV" />
      <DO desc="Available discharge capacity to be discharged in Amp-hours" name="AvlDschAhr" type="DT_MV" />
      <DO desc="State of charge as percentage in relation to the effective energy capacity of the starge resource" name="SocEffAhrPct" type="DT_MV" />
      <DO desc="State of charge deviation between estimated value (calculated) and the real value (measured) in %" name="SocDvPct" type="DT_MV" />
      <DO desc="Rate of battery voltage change over time" name="VolChgRte" type="DT_MV" />
      <DO desc="Instantaneous voltage limit on discharging" name="DschVolLim" type="DT_MV" />
      <DO desc="Type of battery" name="BatTyp" type="DT_ENG_BatteryTypeKind" />
      <DO desc="Maximum battery charge DC current rating" name="ChaAmpMaxRtg" type="DT_ASG" />
      <DO desc="Amp-hour capacity rating" name="AhrRtg" type="DT_ASG" />
      <DO desc="Effective total charge capacity rating in Amp-hours" name="EffAhrRtg" type="DT_ASG" />
      <DO desc="Minimum resting amp-hour capacity rating allowed" name="AhrMinRtg" type="DT_ASG" />
      <DO desc="Maximum battery charge voltage" name="ChaVolMaxRtg" type="DT_ASG" />
      <DO desc="Maximum battery discharge DC current rating" name="DschAmpMxRtg" type="DT_ASG" />
      <DO desc="Rating reflecting the maximum battery voltage while charging" name="ExtVolMaxRtg" type="DT_ASG" />
      <DO desc="Nominal external voltage of the battery" name="ExtVolMaxRtg" type="DT_ASG" />
      <DO desc="Nominal internal voltage of the battery (DC)" name="IntnVolNom" type="DT_ASG" />
      <DO desc="Self discharge power rate" name="SelfDschWRte" type="DT_ASG" />
      <DO desc="Number of cells in parallel" name="CelParCnt" type="DT_ASG" />
      <DO desc="Number of cells in series" name="CelSerCnt" type="DT_ASG" />
      <DO desc="Discharge curve" name="DschWattCrv" type="DT_CSG" />
      <DO desc="Discharge curve by time" name="DschWattTm" type="DT_CSG" />
    </LNodeType>
    <LNodeType id="DT_SBAT" desc="Battery storage supervisory control" class="SBAT">
      <DO desc="If true, Battery Earth Fault is present" name="BatEF" type="DT_SPS" />
      <DO desc="If true, the minimum level of cell voltage has been exceeded" name="CelVolLoAlm" type="DT_SPS" />
      <DO desc="If true, the maximum limit of cell voltage has been exceeded" name="CelVolHiAlm" type="DT_SPS" />
      <DO desc="If true, the battery discharging current has exceeded the maximum threshold" name="DschAmpHiAlm" type="DT_SPS" />
      <DO desc="If true, the warning current threshold during discharging of the battery has been exceeded" name="DschAmpHiWrn" type="DT_SPS" />
      <DO desc="If true, the maximum current threshold during charging of the battery has been exceeded" name="ChaAmpHiAlm" type="DT_SPS" />
      <DO desc="If true, the warning current threshold during charging of the battery has been exceeded" name="ChaAmpHiWrn" type="DT_SPS" />
      <DO desc="If true, the maximum internal temperature threshold of the battery has been exceeded" name="IntnTmpHiAlm" type="DT_SPS" />
      <DO desc="If true, the high internal temperature warning threshold of the battery has been exceeded" name="IntnTmpHiWrn" type="DT_SPS" />
      <DO desc="If true, the minimum internal temperature threshold of the battery has been exceeded" name="IntnTmpLoAlm" type="DT_SPS" />
      <DO desc="If true, the low internal temperature warning threshold of the battery has been exceeded" name="IntnTmpLoWrn" type="DT_SPS" />
      <DO desc="If true, the high level threshold of the temperature external to the battery has been reached" name="ExtTmpHiAlm" type="DT_SPS" />
      <DO desc="If true, the low level threshold of the temperature external to the battery has been reached" name="ExtTmpLoAlm" type="DT_SPS" />
      <DO desc="If true, the high external voltage limit of the battery has been reached" name="ExtVolHiAlm" type="DT_SPS" />
      <DO desc="If true, the low level threshold of the external voltage of the battery has been reached" name="ExtVolLoAlm" type="DT_SPS" />
      <DO desc="Internal Battery current (non DC)" name="IntnA" type="DT_MV" />
      <DO desc="Internal Battery voltage (non DC)" name="IntnV" type="DT_MV" />
      <DO desc="Minimum cell voltage measurement of all cells since last reset" name="CelVolLo" type="DT_MV" />
      <DO desc="Maximum cell voltage measurement of all cells since last reset" name="CelVolHi" type="DT_MV" />
      <DO desc="Maximum temperature of all cells in the battery" name="CelTmpMax" type="DT_MV" />
      <DO desc="Minimum temperature of all cells in the battery" name="CelTmpMin" type="DT_MV" />
      <DO desc="Internal battery temperature in degrees C" name="IntnTmp" type="DT_MV" />
      <DO desc="External battery temperature in degrees C" name="ExtTmp" type="DT_MV" />
      <DO desc="External battery DC voltage" name="ExtVol" type="DT_MV" />
      <DO desc="Internal battery DC voltage" name="IntnVol" type="DT_MV" />
      <DO desc="Initiate reset of the calculated minimum and maximum battery voltage measurements" name="CelVolRs" type="DT_SPC" />
      <DO desc="Alarm threshold for the minimum limit of a battery cell voltage" name="CelVolLoAls" type="DT_ASG" />
      <DO desc="Alarm threshold reflecting the maximum limit of a battery cell voltage" name="CelVolHiAls" type="DT_ASG" />
      <DO desc="High level discharging current threshold alarm setting" name="DSchAmpHiAls" type="DT_ASG" />
      <DO desc="Warning threshold defining the high discharging current warning limit of the battery in A" name="DschAmpHiWrs" type="DT_ASG" />
      <DO desc="High charging current alarm threshold of the battery in A" name="ChaAmpHiAls" type="DT_ASG" />
      <DO desc="Warning threshold defining the high charging current warning limit of the battery in A" name="ChaAmpHiWrs" type="DT_ASG" />
      <DO desc="High internal temperature alarm threshold of the battery in °C" name="IntnTmpHiAls" type="DT_ASG" />
      <DO desc="High internal temperature warning threshold of the battery in °C" name="IntnTmpHiWrs" type="DT_ASG" />
      <DO desc="Low internal temperature alarm threshold of the battery in °C" name="IntnTmpLoAls" type="DT_ASG" />
      <DO desc="Low internal temperature warning threshold of the battery in °C" name="IntnTmpLoWrs" type="DT_ASG" />
      <DO desc="High external battery temperature alarm threshold" name="ExtTmpHiAls" type="DT_ASG" />
      <DO desc="Low external battery temperature alarm threshold" name="ExtTmpLoAls" type="DT_ASG" />
      <DO desc="High level external battery voltage threshold alarm setting" name="ExtVolHiAls" type="DT_ASG" />
      <DO desc="Low level external battery voltage threshold alarm setting" name="ExtVolLoAls" type="DT_ASG" />
    </LNodeType>
    <LNodeType id="DT_DEAO" desc="E-Mobility AC charging outlet" class="DEAO">
      <DO desc="Name plate of external equipment" name="NamPlt" type="DT_LPL" />
      <DO desc="Connection state according to IEC 61851-1" name="ConnSt" type="DT_ENS_EVAC_ConnectionStateKind" />
      <DO desc="Plug present and coupler lock state according to IEC 61851-1" name="PlgStAC" type="DT_ENS_EVAC_PlugStateKind" />
      <DO desc="Capability of the EV cable assembly according to IEC 61851-1" name="CabRgtAC" type="DT_ENS_EVAC_CableCapabilityKind" />
      <DO desc="The rated maximum AC charging current of the outlet" name="ChaARtg" type="DT_ING" />
      <DO desc="Enable digital communication with the EV" name="DigComm" type="DT_SPG" />
      <DO desc="Available AC current (6-80 A) to signal to the EV when not using digital communication" name="ChaAMax" type="DT_ING" />
      <DO desc="Reference to the logical node instance containing information about a connected EV" name="EVRef" type="DT_ORG" />
    </LNodeType>
    <LNodeType id="DT_DEEV" desc="E-Mobility electric vehicle" class="DEEV">
      <DO desc="Name plate of external equipment" name="NamPlt" type="DT_LPL" />
      <DO desc="EV nameplate" name="EVNam" type="DT_DPL" />
      <DO desc="Selected connection type according to IEC 61851-1" name="ConnTypSel" type="DT_ENS_EVConnectionChargingKind" />
      <DO desc="State of charge" name="Soc" type="DT_MV" />
      <DO desc="EVCCId as defined in ISO 15118-2:2014" name="EVId" type="DT_VSG" />
      <DO desc="E-Mobility Account identifier as defined in Annex H.1 of ISO 15118-2:2014" name="EMAId" type="DT_VSG" />
      <DO desc="Departure time, '0' means as soon as possible" name="DptTm" type="DT_TSG" />
      <DO desc="Amount of energy required by the EV until the departure time has been reached or SoC is at 100 %" name="EnAmnt" type="DT_ASG" />
      <DO desc="Maximum voltage supported by the EV. Voltage measured between phase and neutral" name="VMax" type="DT_ASG" />
      <DO desc="Maximum current per phase supported by the EV." name="AMax" type="DT_ASG" />
      <DO desc="Minimum current per phase supported by the EV." name="AMin" type="DT_ASG" />
      <DO desc="Reference to the schedule logical node instance containing information on the charging profile of the EV" name="SchdRef" type="DT_ORG" />
    </LNodeType>
    <DOType id="DT_MV" desc="Measured value" cdc="MV">
      <DA name="mag" bType="Struct" type="AnalogueValue_F" dchg="true" dupd="true" fc="MX" />
      <DA name="q" bType="Quality" qchg="true" fc="MX" />
      <DA name="t" bType="Timestamp" fc="MX" />
      <DA name="units" bType="Struct" type="Unit" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_CMV" desc="Complex measured value" cdc="CMV">
      <DA name="cVal" bType="Struct" type="Vector_F_ang" dchg="true" dupd="true" fc="MX" />
      <DA name="q" bType="Quality" qchg="true" fc="MX" />
      <DA name="t" bType="Timestamp" fc="MX" />
      <DA name="subEna" bType="BOOLEAN" fc="SV" />
      <DA name="subCVal" bType="Struct" type="Vector_F_ang" fc="SV" />
      <DA name="subQ" bType="Quality" fc="SV" />
      <DA name="subID" bType="VisString64" fc="SV" />
      <DA name="units" bType="Struct" type="Unit" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_ING" desc="Integer status setting" cdc="ING">
      <DA name="setVal" bType="INT32" dchg="true" fc="SP" />
      <DA name="minVal" bType="INT32" dchg="true" fc="CF" />
      <DA name="maxVal" bType="INT32" dchg="true" fc="CF" />
      <DA desc="1 … (maxVal - minVal)" name="stepSize" bType="INT32U" dchg="true" fc="CF" />
      <DA name="units" bType="Struct" type="Unit" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_WYE" desc="Phase to ground/neutral related measured values of a three phase system" cdc="WYE">
      <SDO name="phsA" type="DT_CMV" />
      <SDO name="phsB" type="DT_CMV" />
      <SDO name="phsC" type="DT_CMV" />
      <SDO name="neut" type="DT_CMV" />
    </DOType>
    <DOType id="DT_CSG" desc="Curve shape setting" cdc="CSG">
      <DA name="crvPts" Type="ARRAY" fc="SP" />
      <DA name="numPts" bType="UINT16" fc="SP" />
      <DA name="xUnit" bType="Struct" type="Unit" fc="CF" />
      <DA name="yUnit" bType="Struct" type="Unit" fc="CF" />
      <DA name="maxPts" bType="INT16U" fc="CF" />
      <DA name="xD" bType="VisString255" fc="DC" />
      <DA name="yD" bType="VisString255" fc="DC" />
    </DOType>
    <DOType id="DT_ORG" desc="Object reference setting" cdc="ORG">
      <DA name="setSrcRef" bType="ObjRef" dchg="true" fc="SP" />
    </DOType>
    <DOType id="DT_APC" desc="Controllable analogue process value" cdc="APC">
      <DA name="mxVal" bType="Struct" type="AnalogueValue" dchg="true" fc="MX" />
      <DA name="q" bType="Quality" qchg="true" fc="MX" />
      <DA name="t" bType="Timestamp" fc="MX" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
      <DA name="Oper" bType="Struct" type="Oper_Analogue_F" fc="CO" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_Analogue_F" fc="CO" />
      <DA name="Cancel" bType="Struct" type="Cancel_Analogue_F" fc="CO" />
    </DOType>
    <DOType id="DT_INS" desc="Integer status" cdc="INS">
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="stVal" bType="INT32" dchg="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_SwTyp" desc="Enumerated status" cdc="ENS">
      <DA name="stVal" bType="Enum" type="SwTyp" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_BatteryTestResultKind" desc="Enumerated status" cdc="ENS">
      <DA name="stVal" bType="Enum" type="BatteryTestResultKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_SetpointEndKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="SetpointEndKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_AdjustmentKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="AdjustmentKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_EVAC_ConnectionStateKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="EVACConnectionStateKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_EVAC_PlugStateKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="EVACPlugStateKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_EVAC_CableCapabilityKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="EVACCableCapabilityKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_EVConnectionChargingKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="EVConnectionChargingKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_DERUnitkind" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="DERUnitKind" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_ClcMth" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="ClcMth" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_Phasekind" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="PhsKnd" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_Inv_Ctl_Src" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="InvCtlSrc" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_Reactive_Power_kind" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="ReactPowerKind" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_DER_Sync_Stat" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="DERSyncState" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_PVControlStateKind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="PVCtrlStateKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENS_DER_State_Kind" desc="Enumerated status setting" cdc="ENS">
      <DA name="stVal" bType="Enum" type="DERStateKind" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_PF_Sign" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="PFSignKind" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_Inv_Switch_Kind" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="InvSwKind" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_PV_Assembly" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="PVAssembly" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_PV_Config" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="PVConfig" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_ENG_PV_Gnd_Conn" desc="Enumerated status setting" cdc="ENG">
      <DA name="setVal" bType="Enum" type="PVGndCnfg" dchg="true" dupd="true" fc="ST" />
    </DOType>
    <DOType id="DT_SAV" desc="Sampled value" cdc="SAV">
      <DA name="instMag" bType="Struct" type="AnalogueValue_F" fc="MX" />
      <DA name="q" bType="Quality" qchg="true" fc="MX" />
    </DOType>
    <DOType id="DT_ENC_Mod" desc="Controllable enumerated status" cdc="ENC">
      <DA name="stVal" bType="Enum" type="Mod" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_ENC_PVArrayControlModeKind" desc="Controllable enumerated status" cdc="ENC">
      <DA name="stVal" bType="Enum" type="PVArrayControlModeKind" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_LPL" desc="Logical node name plate" cdc="LPL">
      <DA name="vendor" bType="VisString255" fc="DC" />
      <DA name="swRev" bType="VisString255" fc="DC" />
      <DA name="d" bType="VisString255" fc="DC" />
      <DA name="configRev" bType="VisString255" fc="DC" />
    </DOType>
    <DOType id="DT_SPG" desc="Single point setting" cdc="SPG">
      <DA name="setVal" btype="BOOLEAN" dchg="true" fc="SP" />
    </DOType>
    <DOType id="DT_VSG" desc="Visible string setting group" cdc="VSG">
      <DA name="setVal" bType="VisString255" dchg="true" fc="SP" />
    </DOType>
    <DOType id="DT_DPL" desc="Device name plate" cdc="DPL">
      <DA name="vendor" bType="VisString255" fc="DC" />
      <DA name="hwRev" bType="VisString255" fc="DC" />
      <DA name="swRev" bType="VisString255" fc="DC" />
      <DA name="serNum" bType="VisString255" fc="DC" />
      <DA name="model" bType="VisString255" fc="DC" />
      <DA name="location" bType="VisString255" fc="DC" />
      <DA name="name" bType="VisString255" fc="DC" />
      <DA name="owner" bType="VisString255" fc="DC" />
    </DOType>
    <DOType id="DT_ENS_Health" desc="Enumerated status" cdc="ENS">
      <DA name="stVal" bType="Enum" type="Health" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ACD" desc="Directional protection activation information" cdc="ACD">
      <DA name="general" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="dirGeneral" bType="Enum" type="dir" dchg="true" fc="ST" />
      <DA name="phsA" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="dirPhsA" bType="Enum" type="DT_dir" dchg="true" fc="ST" />
      <DA name="phsB" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="dirPhsB" bType="Enum" type="DT_dir" dchg="true" fc="ST" />
      <DA name="phsC" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="dirPhsC" bType="Enum" type="DT_dir" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_TSG" desc="Time setting group" cdc="TSG">
      <DA name="setTm" bType="Timestamp" dchg="true" fc="SP" />
      <DA name="setCal" bType="CalenderTime" dchg="true" fc="SP" />
    </DOType>
    <DOType id="DT_ACT" desc="Protection activation information" cdc="ACT">
      <DA name="general" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="phsA" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="phsB" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="phsC" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_SPS" desc="Single point status" cdc="SPS">
      <DA name="stVal" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_BCR" desc="Binary counter reading" cdc="BCR">
      <DA name="actVal" bType="INT64" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="pulsQty" bType="FLOAT32" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_SPC" desc="Controllable single point" cdc="SPC">
      <DA desc="FALSE | TRUE" name="stVal" bType="BOOLEAN" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
      <DA name="Oper" bType="Struct" type="Oper_BOOLEAN" fc="CO" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_BOOLEAN" fc="CO" />
      <DA name="Cancel" bType="Struct" type="Cancel_BOOLEAN" fc="CO" />
    </DOType>
    <DOType id="DT_DPC" desc="Controllable double point" cdc="DPC">
      <DA name="Cancel" bType="Struct" type="Cancel_BOOLEAN" fc="CO" />
      <DA name="Oper" bType="Struct" type="Oper_BOOLEAN" fc="CO" />
      <DA name="origin" bType="Struct" type="Originator" fc="ST" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_BOOLEAN" fc="CO" />
      <DA name="stVal" bType="Dbpos" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" fc="CF" />
    </DOType>
    <DOType id="DT_INC" desc="Controllable integer status" cdc="INC">
      <DA name="stVal" bType="INT32" dchg="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
      <DA name="Oper" bType="Struct" type="Oper_INT32" fc="CO" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_INT32" fc="CO" />
      <DA name="Cancel" bType="Struct" type="Cancel_INT32" fc="CO" />
    </DOType>
    <DOType id="DT_BAC" desc="Binary controlled analog process value" cdc="BAC">
      <DA name="mxVal" bType="Struct" type="AnalogueValue" dchg="true" fc="MX" />
      <DA name="q" bType="Quality" qchg="true" fc="MX" />
      <DA name="t" bType="Timestamp" fc="MX" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
      <DA name="Oper" bType="Struct" type="Oper_CODED_ENUM" fc="CO" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_Analogue_F" fc="CO" />
      <DA name="Cancel" bType="Struct" type="Cancel_Analogue_F" fc="CO" />
    </DOType>
    <DOType id="DT_ASG" desc="Analogue setting" cdc="ASG">
      <DA name="setMag" bType="Struct" type="AnalogueValue_F" dchg="true" fc="SP" />
      <DA name="units" bType="Struct" type="Unit" dchg="true" fc="CF" />
    </DOType>
    <DOType id="DT_ENS_Beh" desc="Enumerated status" cdc="ENS">
      <DA name="stVal" bType="Enum" type="Beh" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
    </DOType>
    <DOType id="DT_ENC_Mod" desc="Enumerated status" cdc="ENC">
      <DA name="stVal" bType="Enum" type="Mod" dchg="true" dupd="true" fc="ST" />
      <DA name="q" bType="Quality" qchg="true" fc="ST" />
      <DA name="t" bType="Timestamp" fc="ST" />
      <DA name="ctlModel" bType="Enum" type="ctlModel" dchg="true" fc="CF" />
      <DA name="Oper" bType="Struct" type="Oper_INT32" fc="CO" />
      <DA name="SBO" bType="VisString129" fc="CO" />
      <DA name="SBOw" bType="Struct" type="SBOw_INT32" fc="CO" />
      <DA name="Cancel" bType="Struct" type="Cancel_INT32" fc="CO" />
    </DOType>
    <DAType id="Vector_F_ang">
      <BDA name="mag" bType="Struct" type="AnalogueValue_F" />
      <BDA name="ang" bType="Struct" type="AnalogueValue_F" />
    </DAType>
    <DAType id="Cancel_BOOLEAN">
      <BDA name="ctlVal" bType="BOOLEAN" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
    </DAType>
    <DAType id="Oper_BOOLEAN">
      <BDA name="ctlVal" bType="BOOLEAN" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
      <BDA name="Check" bType="Check" />
    </DAType>
    <DAType id="SBOw_BOOLEAN">
      <BDA name="ctlVal" bType="BOOLEAN" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
      <BDA name="Check" bType="Check" />
    </DAType>
    <DAType id="Oper_INT32">
      <BDA name="ctlVal" bType="INT32" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
      <BDA name="Check" bType="Check" />
    </DAType>
    <DAType id="Oper_CODED_ENUM">
      <BDA name="ctlVal" bType="Enum" type="Tcmd" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
      <BDA name="Check" bType="Check" />
    </DAType>
    <DAType id="SBOw_INT32">
      <BDA name="ctlVal" bType="INT32" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
      <BDA name="Check" bType="Check" />
    </DAType>
    <DAType id="Originator">
      <BDA name="orCat" bType="Enum" type="orCategory" />
      <BDA name="orIdent" bType="Octet64" />
    </DAType>
    <DAType id="Cancel_INT32">
      <BDA name="ctlVal" bType="INT32" />
      <BDA name="origin" bType="Struct" type="Originator" />
      <BDA name="ctlNum" bType="INT8U" />
      <BDA name="T" bType="Timestamp" />
      <BDA name="Test" bType="BOOLEAN" />
    </DAType>
    <DAType id="AnalogueValue_F">
      <BDA name="f" bType="FLOAT32" />
    </DAType>
    <DAType id="Unit">
      <BDA name="SIUnit" bType="Enum" type="SIUnit" />
    </DAType>
    <EnumType id="Tcmd">
      <EnumVal ord="0">stop</EnumVal>
      <EnumVal ord="1">lower</EnumVal>
      <EnumVal ord="2">higher</EnumVal>
      <EnumVal ord="3">reserved</EnumVal>
    </EnumType>
    <EnumType id="EVACConnectionStateKind">
      <EnumVal ord="1">State A</EnumVal>
      <EnumVal ord="2">State B</EnumVal>
      <EnumVal ord="3">State C</EnumVal>
      <EnumVal ord="4">State D</EnumVal>
      <EnumVal ord="5">State E</EnumVal>
      <EnumVal ord="6">State F</EnumVal>
      <ENumVal ord="98">Not applicable / Unknown </ENumVal>
    </EnumType>
    <EnumType id="EVACPlugStateKind">
      <EnumVal ord="1">Disconnected</EnumVal>
      <EnumVal ord="2">Connected and unlocked</EnumVal>
      <EnumVal ord="3">Connected and locked</EnumVal>
      <EnumVal ord="4">Connected</EnumVal>
      <EnumVal ord="98">Not applicable / Unknown </EnumVal>
    </EnumType>
    <EnumType id="EVACCableCapabilityKind">
      <EnumVal ord="1">13A</EnumVal>
      <EnumVal ord="2">20A</EnumVal>
      <EnumVal ord="3">32A</EnumVal>
      <EnumVal ord="4">63/70A</EnumVal>
    </EnumType>
    <EnumType id="EVConnectionChargingKind">
      <EnumVal ord="1">Single Phase</EnumVal>
      <EnumVal ord="2">Three Phase</EnumVal>
      <EnumVal ord="3">System A</EnumVal>
      <EnumVal ord="4">System B</EnumVal>
      <EnumVal ord="5">System C</EnumVal>
      <EnumVal ord="98">Not applicable / Unknown</EnumVal>
    </EnumType>
    <EnumType id="BatteryTestResultKind">
      <EnumVal ord="1">success</EnumVal>
      <EnumVal ord="2">fault (bad)</EnumVal>
      <EnumVal ord="99">unknown</EnumVal>
    </EnumType>
    <EnumType id="SwTyp">
      <EnumVal ord="1">Load Break Switch</EnumVal>
      <EnumVal ord="2">Disconnector</EnumVal>
      <EnumVal ord="3">Earthing Switch</EnumVal>
      <EnumVal ord="4">High Speed Earthing Switch</EnumVal>
    </EnumType>
    <EnumType id="SetpointEndKind">
      <EnumVal ord="1">Ended normally</EnumVal>
      <EnumVal ord="2">Ended with overshoot</EnumVal>
      <EnumVal ord="3">Cancelled: measurement was deviating</EnumVal>
      <EnumVal ord="4">Cancelled: loss of communication with dispatch centre</EnumVal>
      <EnumVal ord="5">Cancelled: loss of communication with local area network</EnumVal>
      <EnumVal ord="6">Cancelled: loss of communication with local interface</EnumVal>
      <EnumVal ord="7">Cancelled: timeout</EnumVal>
      <EnumVal ord="8">Cancelled: voluntarily</EnumVal>
      <EnumVal ord="9">Cancelled: noisy environments</EnumVal>
      <EnumVal ord="10">Cancelled: material failure</EnumVal>
      <EnumVal ord="11">Cancelled: new set-point request</EnumVal>
      <EnumVal ord="12">Cancelled: improper environment (blockage)</EnumVal>
      <EnumVal ord="13">Cancelled: stability time was reached</EnumVal>
      <EnumVal ord="14">Cancelled: Immobilisation time was reached</EnumVal>
      <EnumVal ord="15">Cancelled: equipment was in the wrong mode</EnumVal>
      <EnumVal ord="16">Unknown causes</EnumVal>
    </EnumType>
    <EnumType id="AdjustmentKind">
      <EnumVal ord="1">Completed</EnumVal>
      <EnumVal ord="2">Cancelled</EnumVal>
      <EnumVal ord="3">New adjustments</EnumVal>
      <EnumVal ord="4">Under way</EnumVal>
    </EnumType>
    <EnumType id="Dbpos">
      <EnumVal ord="0">intermediate-state</EnumVal>
      <EnumVal ord="1">off</EnumVal>
      <EnumVal ord="2">on</EnumVal>
      <EnumVal ord="3">bad-state</EnumVal>
    </EnumType>
    <EnumType id="Mod">
      <EnumVal ord="1">on</EnumVal>
      <EnumVal ord="2">on-blocked</EnumVal>
      <EnumVal ord="3">test</EnumVal>
      <EnumVal ord="4">test/blocked</EnumVal>
      <EnumVal ord="5">off</EnumVal>
    </EnumType>
    <EnumType id="Health">
      <EnumVal ord="1">Ok</EnumVal>
      <EnumVal ord="2">Warning</EnumVal>
      <EnumVal ord="3">Alarm</EnumVal>
    </EnumType>
    <EnumType id="dir">
      <EnumVal ord="0">unknown</EnumVal>
      <EnumVal ord="1">forward</EnumVal>
      <EnumVal ord="2">backward</EnumVal>
      <EnumVal ord="3">both</EnumVal>
    </EnumType>
    <EnumType id="DT_dir">
      <EnumVal ord="1">unknown</EnumVal>
      <EnumVal ord="2">forward</EnumVal>
      <EnumVal ord="3">backward</EnumVal>
    </EnumType>
    <EnumType id="ctlModel">
      <EnumVal ord="0">status-only</EnumVal>
      <EnumVal ord="1">direct-with-normal-security</EnumVal>
      <EnumVal ord="2">sbo-with-normal-security</EnumVal>
      <EnumVal ord="3">direct-with-enhanced-security</EnumVal>
      <EnumVal ord="4">sbo-with-enhanced-security</EnumVal>
    </EnumType>
    <EnumType id="orCategory">
      <EnumVal ord="0">not-supported</EnumVal>
      <EnumVal ord="1">bay-control</EnumVal>
      <EnumVal ord="2">station-control</EnumVal>
      <EnumVal ord="3">remote-control</EnumVal>
      <EnumVal ord="4">automatic-bay</EnumVal>
      <EnumVal ord="5">automatic-station</EnumVal>
      <EnumVal ord="6">automatic-remote</EnumVal>
      <EnumVal ord="7">maintenance</EnumVal>
      <EnumVal ord="8">process</EnumVal>
    </EnumType>
    <EnumType id="SIUnit">
      <EnumVal ord="1" />
      <EnumVal ord="2">m</EnumVal>
      <EnumVal ord="3">kg</EnumVal>
      <EnumVal ord="4">s</EnumVal>
      <EnumVal ord="5">A</EnumVal>
      <EnumVal ord="6">K</EnumVal>
      <EnumVal ord="7">mol</EnumVal>
      <EnumVal ord="8">cd</EnumVal>
      <EnumVal ord="9">deg</EnumVal>
      <EnumVal ord="10">rad</EnumVal>
      <EnumVal ord="11">sr</EnumVal>
      <EnumVal ord="21">Gy</EnumVal>
      <EnumVal ord="22">Bq</EnumVal>
      <EnumVal ord="23">°C</EnumVal>
      <EnumVal ord="24">Sv</EnumVal>
      <EnumVal ord="25">F</EnumVal>
      <EnumVal ord="26">C</EnumVal>
      <EnumVal ord="27">S</EnumVal>
      <EnumVal ord="28">H</EnumVal>
      <EnumVal ord="29">V</EnumVal>
      <EnumVal ord="30">ohm</EnumVal>
      <EnumVal ord="31">J</EnumVal>
      <EnumVal ord="32">N</EnumVal>
      <EnumVal ord="33">Hz</EnumVal>
      <EnumVal ord="34">lx</EnumVal>
      <EnumVal ord="35">Lm</EnumVal>
      <EnumVal ord="36">Wb</EnumVal>
      <EnumVal ord="37">T</EnumVal>
      <EnumVal ord="38">W</EnumVal>
      <EnumVal ord="39">Pa</EnumVal>
      <EnumVal ord="41">m²</EnumVal>
      <EnumVal ord="42">m³</EnumVal>
      <EnumVal ord="43">m/s</EnumVal>
      <EnumVal ord="44">m/s²</EnumVal>
      <EnumVal ord="45">m³/s</EnumVal>
      <EnumVal ord="46">m/m³</EnumVal>
      <EnumVal ord="47">M</EnumVal>
      <EnumVal ord="48">kg/m³</EnumVal>
      <EnumVal ord="49">m²/s</EnumVal>
      <EnumVal ord="50">W/m K</EnumVal>
      <EnumVal ord="51">J/K</EnumVal>
      <EnumVal ord="52">ppm</EnumVal>
      <EnumVal ord="53">1/s</EnumVal>
      <EnumVal ord="54">rad/s</EnumVal>
      <EnumVal ord="61">VA</EnumVal>
      <EnumVal ord="62">Watts</EnumVal>
      <EnumVal ord="63">VAr</EnumVal>
      <EnumVal ord="64">phi</EnumVal>
      <EnumVal ord="65">cos(phi)</EnumVal>
      <EnumVal ord="66">Vs</EnumVal>
      <EnumVal ord="67">V²</EnumVal>
      <EnumVal ord="68">As</EnumVal>
      <EnumVal ord="69">A²</EnumVal>
      <EnumVal ord="70">A²t</EnumVal>
      <EnumVal ord="71">VAh</EnumVal>
      <EnumVal ord="72">Wh</EnumVal>
      <EnumVal ord="73">VArh</EnumVal>
      <EnumVal ord="74">V/Hz</EnumVal>
      <EnumVal ord="75">Hz/s</EnumVal>
      <EnumVal ord="76">char</EnumVal>
      <EnumVal ord="77">char/s</EnumVal>
      <EnumVal ord="78">kgm²</EnumVal>
      <EnumVal ord="79">dB</EnumVal>
    </EnumType>
    <EnumType id="Beh">
      <EnumVal ord="1">on</EnumVal>
      <EnumVal ord="2">on-blocked</EnumVal>
      <EnumVal ord="3">test</EnumVal>
      <EnumVal ord="4">test/blocked</EnumVal>
      <EnumVal ord="5">off</EnumVal>
    </EnumType>
    <EnumType id="ClcMth">
      <EnumVal ord="1">unspecified</EnumVal>
      <EnumVal ord="2">true-rms</EnumVal>
      <EnumVal ord="3">peak-fundamental</EnumVal>
      <EnumVal ord="4">rms-fundamental</EnumVal>
      <EnumVal ord="5">min</EnumVal>
      <EnumVal ord="6">max</EnumVal>
      <EnumVal ord="7">avg</EnumVal>
      <EnumVal ord="8">sdv</EnumVal>
      <EnumVal ord="9">prediction</EnumVal>
      <EnumVal ord="10">rate</EnumVal>
    </EnumType>
    <EnumType id="PFSignKind">
      <EnumVal ord="1">IEC</EnumVal>
      <EnumVal ord="2">EEI</EnumVal>
    </EnumType>
    <EnumType id="PVConfig">
      <EnumVal ord="1">Flat plate</EnumVal>
      <EnumVal ord="2">Concentrating</EnumVal>
      <EnumVal ord="98">Not applicable or unknown</EnumVal>
    </EnumType>
    <EnumType id="PVAssembly">
      <EnumVal ord="1">Array</EnumVal>
      <EnumVal ord="2">Sub-Array</EnumVal>
      <EnumVal ord="3">String</EnumVal>
      <EnumVal ord="4">Module</EnumVal>
      <EnumVal ord="5">Plant</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="PVGndCnfg">
      <EnumVal ord="1">Positive ground</EnumVal>
      <EnumVal ord="2">Negative ground</EnumVal>
      <EnumVal ord="3">Not grounded</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="DERSyncState">
      <EnumVal ord="1">Unavailable to connect</EnumVal>
      <EnumVal ord="2">Not synchronized, available to connect</EnumVal>
      <EnumVal ord="3">In synchronization process</EnumVal>
      <EnumVal ord="4">Synchronized and not connected</EnumVal>
      <EnumVal ord="5">Synchronized and connected</EnumVal>
      <EnumVal ord="6">Synchronization failure</EnumVal>
      <EnumVal ord="7">Disconnecting from grid</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="DERStateKind">
      <EnumVal ord="1">on but disconnected and not ready</EnumVal>
      <EnumVal ord="2">starting up</EnumVal>
      <EnumVal ord="3">disconnected and available</EnumVal>
      <EnumVal ord="4">disconnected and authorized</EnumVal>
      <EnumVal ord="5">synchronizing</EnumVal>
      <EnumVal ord="6">running</EnumVal>
      <EnumVal ord="7">stopping and disconnecting under emergency conditions</EnumVal>
      <EnumVal ord="8">stopping</EnumVal>
      <EnumVal ord="9">disconnected and blocked</EnumVal>
      <EnumVal ord="10">disconnected and in maintenance</EnumVal>
      <EnumVal ord="11">failed</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="InvSwKind">
      <EnumVal ord="1">Field effect transistor</EnumVal>
      <EnumVal ord="2">Insulated gate bipolar transistor</EnumVal>
      <EnumVal ord="3">Thyristor</EnumVal>
      <EnumVal ord="4">Gate turn off thyristor</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="InvCtlSrc">
      <EnumVal ord="1">Current-source inverter (CSI)</EnumVal>
      <EnumVal ord="2">Voltage-controlled voltage-source inverter (VC-VSI)</EnumVal>
      <EnumVal ord="3">Current-controlled voltage-source inverter (CC-VSI)</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="ReactPowerKind">
      <EnumVal ord="1">Reactive power in percent of WMax</EnumVal>
      <EnumVal ord="2">Reactive power in percent of VArMax</EnumVal>
      <EnumVal ord="3">Reactive power in percent of VArAvl</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="PhsKnd">
      <EnumVal ord="1">Single phase to neutral</EnumVal>
      <EnumVal ord="2">Split phase</EnumVal>
      <EnumVal ord="3">2-phase</EnumVal>
      <EnumVal ord="4">3-phase delta</EnumVal>
      <EnumVal ord="5">3-phase wye / 4-wires</EnumVal>
      <EnumVal ord="6">3-physe wye / 5-wires</EnumVal>
      <EnumVal ord="9">DC</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="DERUnitKind">
      <EnumVal ord="1">Diesel / gas engine</EnumVal>
      <EnumVal ord="2">Gas Turbine engine</EnumVal>
      <EnumVal ord="3">PV</EnumVal>
      <EnumVal ord="4">PV plus storage</EnumVal>
      <EnumVal ord="5">Lithium Ion Battery Storage</EnumVal>
      <EnumVal ord="6">Fuel cell</EnumVal>
      <EnumVal ord="7">Hydro generator</EnumVal>
      <EnumVal ord="8">Wind turbine</EnumVal>
      <EnumVal ord="9">Flow battery storage</EnumVal>
      <EnumVal ord="10">Air compression storage</EnumVal>
      <EnumVal ord="11">Flywheel storage</EnumVal>
      <EnumVal ord="12">Capacitor storage</EnumVal>
      <EnumVal ord="13">Vehicle-to-Grid (VSG)</EnumVal>
      <EnumVal ord="50">Mixed,hybrid DER</EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
    <EnumType id="PVCtrlStateKind">
      <EnumVal ord="1">Not ready</EnumVal>
      <EnumVal ord="2">Asleep</EnumVal>
      <EnumVal ord="3">Awaking up</EnumVal>
      <EnumVal ord="4">Awake</EnumVal>
      <EnumVal ord="5">Shutdown / Sleep test</EnumVal>
      <EnumVal ord="6">Under test</EnumVal>
    </EnumType>
    <EnumType id="PVArrayControlModeKind">
      <EnumVal ord="1">Maximum power point tracking (MPPT)</EnumVal>
      <EnumVal ord="2">Power limiter controller</EnumVal>
      <EnumVal ord="3">DC current limit</EnumVal>
      <EnumVal ord="4">Array voltage control </EnumVal>
      <EnumVal ord="98">Not applicable or not known</EnumVal>
    </EnumType>
  </DataTypeTemplates>
</SCL>
